"""All classes related to the use and control of XQEMU"""

from contextlib import AbstractContextManager
from ftplib import FTP
import os
import subprocess
from typing import NamedTuple, Optional, Sequence, Tuple
import uuid

from qmp import QEMUMonitorProtocol

from .._utils import retry_every, UnusedPort

# Because pyxboxtest.xqemu imports XQEMUXboxAppRunner pytest falls over...
# pytype: disable=pyi-error
from ._xqemu_temporary_directories import get_temp_dirs
from . import (
    XQEMUFTPClient,
    XQEMUKDCapturer,
    XQEMUNetworkForwardRule,
    XQEMURAMSize,
    XQEMUXboxControllerButtons,
)

# pytype: enable=pyi-error


class _XQEMUXboxAppRunnerGlobalParams(NamedTuple):
    """For internal use only! Should only be set by the pytest plugin"""

    mcpx_rom_filename: str
    xbox_bios_filename: str
    headless: bool


class XQEMUXboxAppRunner(AbstractContextManager):
    """Run an app in XQEMU with this context manager. The app is killed at the
    end.
    Provides facilities network forwarding, screenshots, kernel debug capture
    and sending controller input to XQEMU
    """

    """For internal use only! Should only be set by the pytest plugin"""
    _global_params: Optional[_XQEMUXboxAppRunnerGlobalParams] = None

    def __init__(
        self,
        hdd_filename: Optional[str] = None,
        dvd_filename: Optional[str] = None,
        network_forward_rules: Optional[Tuple[XQEMUNetworkForwardRule, ...]] = None,
        ram_size: XQEMURAMSize = XQEMURAMSize.RAM64m,
        force_headless: bool = False,
    ):
        """:param force_headless: only use this if you are doing something
        fancy like using a "hidden" Xbox app to do some test setup!
        """
        if XQEMUXboxAppRunner._global_params is None:
            raise RuntimeError(
                "Trying to instantiate before the bios and mcpx rom are set!"
                + " Are you doing something globally that should be in a fixture?"
            )

        self._qemu_monitor_instance = None
        self._kd_capturer_instance = None
        headless = force_headless or XQEMUXboxAppRunner._global_params.headless

        # need some way of ensuring that only one process at a time can do this
        # so as to avoid having multiple processes using the same ports
        # with parallel test execution
        mcpx_rom = XQEMUXboxAppRunner._global_params.mcpx_rom_filename
        xbox_bios = XQEMUXboxAppRunner._global_params.xbox_bios_filename

        # To allow parallel test execution different instances must be using different ports
        self._ftp_forward_port = UnusedPort()
        self._kd_forward_port = UnusedPort()
        self._qemu_monitor_forward_port = UnusedPort()

        self._xqemu_args = (
            "xqemu",
            "-cpu",
            "pentium3",
            "-machine",
            f"xbox,bootrom={mcpx_rom},short_animation",
            "-m",
            ram_size.value,
            "-bios",
            xbox_bios,
            "-device",  # Is this the right controller connection code?
            "usb-hub,port=3",
            "-device",
            "usb-xbox-gamepad,port=3.1",
            "-device",
            "lpc47m157",
            "-net",
            "nic,model=nvnet",
            "-net",
            f"user,hostfwd=tcp:127.0.0.1:{self._ftp_forward_port.port_number}-:21",
            "-serial",
            f"tcp::{self._kd_forward_port.port_number},server",
            "-qmp",
            f"tcp::{self._qemu_monitor_forward_port.port_number},server,nowait",
        )
        if headless:
            self._xqemu_args += ("-display", "egl-headless")

        if hdd_filename is not None:
            self._xqemu_args += ("-drive", f"file={hdd_filename},index=0,media=disk")
        if dvd_filename is not None:
            self._xqemu_args += ("-drive", f"index=1,media=cdrom,file={dvd_filename}")

        print("xqemu parameters: ", self._xqemu_args)

        self._app = None

    def get_ftp_client(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> FTP:
        """This assumes that an FTP client is actually running in the app..."""
        ftp_client = XQEMUFTPClient(self._ftp_forward_port.port_number)
        if username is not None and password is not None:
            ftp_client.login(username, password)
        return ftp_client

    def press_controller_buttons(
        self,
        buttons: Sequence[XQEMUXboxControllerButtons],
        hold_time: Optional[int] = None,
    ) -> None:
        """Press buttons on the virtual xbox controller"""
        args = {"keys": [{"type": "qcode", "data": key.value} for key in buttons]}
        if hold_time is not None:
            args["hold-time"] = hold_time
        print(args)
        self._get_qemu_monitor().command("send-key", **args)

    def reset_xbox(self) -> None:
        """Reset the Xbox

        It will then load whatever software the kernel is configured to load
        on reset. It will probably reload whatever software started
        running when you first started running this instance.
        """
        print(self._get_qemu_monitor().command("system_reset"))

    def save_screenshot_non_temp(self, filename: str) -> None:
        """Save a screenshot in ppm format in some place

        You should probably use save_screenshot, only use this method if you
        want to keep the screenshots after the test e.g. if you are using this
        lib to keep screenshots up to date for each release at the same time
        as testing.
        """
        _, file_extension = os.path.splitext(filename)
        if file_extension.lower() != ".ppm":
            raise ValueError("File extension must be ppm!")

        self._get_qemu_monitor().command("screendump", filename=filename)

    def save_screenshot(self, filename: Optional[str] = None) -> str:
        """Save a screenshot in ppm format
        The screenshot is saved in the temporary dir for this test
        :param filename: if not given a unique filename will be generated
        :returns: the path to the screenshot
        """
        if filename is None:
            filename = uuid.uuid4().hex + ".ppm"
        screenshot_path = os.path.join(get_temp_dirs().screenshots_dir, filename)
        self.save_screenshot_non_temp(screenshot_path)
        return screenshot_path

    def get_kd_capturer(self) -> XQEMUKDCapturer:
        """Can be used to retrieve text from the serial port"""
        return self._kd_capturer_instance

    def _get_qemu_monitor(self) -> QEMUMonitorProtocol:
        """:returns: a qemu monitor thats used to communicate with XQEMU"""
        if self._qemu_monitor_instance is None:
            self._qemu_monitor_instance = QEMUMonitorProtocol(
                ("", self._qemu_monitor_forward_port.port_number)
            )
            # If called too early it won't be able to connect first try as XQEMU is not ready yet
            retry_every(self._qemu_monitor_instance.connect)
        return self._qemu_monitor_instance

    def __enter__(self):
        self._app = subprocess.Popen(self._xqemu_args)
        self._kd_capturer_instance = XQEMUKDCapturer(self._kd_forward_port.port_number)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Uncaptured KD output:")
        self._kd_capturer_instance.get_all()  # Will log it

        self._kd_capturer_instance.close()
        if self._qemu_monitor_instance is not None:
            self._qemu_monitor_instance.close()
        self._app.terminate()
        # Wait so that we can be sure that we can use the HDD image elsewhere
        self._app.wait()
