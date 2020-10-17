"""All classes related to the use and control of XQEMU"""

from contextlib import AbstractContextManager
from ftplib import FTP
import subprocess
from typing import Any, Dict, Optional

from qmp import QEMUMonitorProtocol

from .._utils import get_unused_ports, retry_every
from . import XQEMURAMSize, XQEMUFTPClient, XQEMUKDCapturer


def _set_headless(headless: bool) -> None:
    """For internal use only!"""
    global _HEADLESS
    _HEADLESS = headless


class XQEMUXboxAppRunner(AbstractContextManager):
    """Run an app in XQEMU with this context manager. The app is killed at the end.
    Provides read/write access to the harddrive, screenshot functionality and the
    ability to send controller input to the console.
    """

    def __init__(
        self,
        hdd_filename: Optional[str] = None,
        dvd_filename: Optional[str] = None,
        ram_size: XQEMURAMSize = XQEMURAMSize.RAM64m,
        force_headless: bool = False,
    ):
        """:param force_headless: not reccomended for general purpose use!"""
        self._hdd_filename = hdd_filename
        self._dvd_filename = dvd_filename
        self._ram_size = ram_size
        self._qemu_monitor_instance = None
        self._kd_capturer_instance = None
        self._headless = force_headless or _HEADLESS

    def get_app_suprocess(self):
        return self._app

    def get_ftp_client(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 60.0,
    ) -> FTP:
        """This assumes that an FTP client is actually running in the app..."""
        ftp_client = XQEMUFTPClient(self._ftp_forward_port)
        if username is not None and password is not None:
            ftp_client.login(username, password)
        ftp_client.dir()
        return ftp_client

    def press_key(self, key: str, hold_time: Optional[int] = None) -> None:
        # Need to figure out how to set hold time :s
        args: Dict[str, Any] = {"keys": [{"type": "qcode", "data": key}]}
        if hold_time is not None:
            args["hold-time"] = hold_time
        self._get_qemu_monitor().command("send-key", **args)

    def save_screenshot(self, filename: str) -> None:
        self._get_qemu_monitor().command("screendump", filename=filename)

    def get_kd_capturer(self) -> XQEMUKDCapturer:
        if self._kd_capturer_instance is None:
            self._kd_capturer_instance = XQEMUKDCapturer(self._kd_forward_port)
        return self._kd_capturer_instance

    def _get_qemu_monitor(self) -> QEMUMonitorProtocol:
        if self._qemu_monitor_instance is None:
            self._qemu_monitor_instance = QEMUMonitorProtocol(
                ("", self._qemu_monitor_forward_port)
            )
            # If called too early it won't be able to connect first try as XQEMU is not ready yet
            retry_every(lambda: self._qemu_monitor_instance.connect())
        return self._qemu_monitor_instance

    def __enter__(self):
        # need some way of ensuring that only one process at a time can do this
        # so as to avoid having multiple processes using the same ports
        # with parallel test execution
        mcpx_rom = "/home/josh/.xqemu_files/mcpx_1.0.bin"
        xqemu_binary = "/bin/xqemu"
        xbox_bios = "/home/josh/.xqemu_files/Complex_4627.bin"

        # To allow parallel test execution different instances must be using different ports
        (
            self._ftp_forward_port,
            self._kd_forward_port,
            self._qemu_monitor_forward_port,
        ) = get_unused_ports(3)

        xqemu_args = (
            xqemu_binary,
            "-cpu",
            "pentium3",
            "-machine",
            f"xbox,bootrom={mcpx_rom},short_animation",
            "-m",
            self._ram_size.value,
            "-bios",
            xbox_bios,
            "-device",
            "usb-xbox-gamepad",
            "-device",
            "lpc47m157",
            "-net",
            "nic,model=nvnet",
            "-net",
            f"user,hostfwd=tcp:127.0.0.1:{self._ftp_forward_port}-:21",
            "-serial",
            f"tcp::{self._kd_forward_port},server,nowait",
            "-qmp",
            f"tcp::{self._qemu_monitor_forward_port},server,nowait",
        )
        if self._headless:
            xqemu_args += ("-display", "egl-headless")

        if self._hdd_filename is not None:
            xqemu_args += ("-drive", f"file={self._hdd_filename},index=0,media=disk")
        if self._dvd_filename is not None:
            xqemu_args += ("-drive", f"index=1,media=cdrom,file={self._dvd_filename}")
        self._app = subprocess.Popen(xqemu_args)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._qemu_monitor_instance is not None:
            self._qemu_monitor_instance.close()
        if self._kd_capturer_instance is not None:
            self._kd_capturer_instance.close()
        self._app.kill()
