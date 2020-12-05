"""Tests for :py:class:`~pyxboxtest.xqemu.XQEMUXboxAppRunner`"""
import random
from typing import NamedTuple, Optional, Tuple

import pytest

from pyxboxtest.xqemu import XQEMURAMSize, XQEMUXboxAppRunner
from pyxboxtest.xqemu.xqemu_xbox_app_runner import _XQEMUXboxAppRunnerGlobalParams


@pytest.fixture(autouse=True)
def mocked_kd_capturer(mocker):
    """The KD capturer will try to connect to a socket that does not exist
    so we mock :py:class:`~pyxboxtest.xqemu.XQEMUKDCapturer`
    """
    return mocker.patch("pyxboxtest.xqemu.xqemu_xbox_app_runner.XQEMUKDCapturer")


@pytest.fixture
def mocked_unused_port(mocker):
    """It is very useful to control the ports that are returned so that we can
    test the parameters passed to xqemu more easily so we mock
    :py:class:`~pyxboxtest.xqemu._utils.UnusedPort`
    """
    return mocker.patch("pyxboxtest.xqemu.xqemu_xbox_app_runner.UnusedPort")


@pytest.fixture
def mocked_xqemu_firmware(mocker):
    """mock :py:class:`~pyxboxtest.xqemu.XQEMUFirmware` so that we can control
    what parameters is returns
    """
    return mocker.patch("pyxboxtest.xqemu.xqemu_xbox_app_runner.XQEMUFirmware")


def get_common_params(
    xqemu_binary: str,
    firmware_params: Tuple[str, ...],
    ram_size: XQEMURAMSize,
    ftp_forward_port: int,
    kd_forward_port: int,
    qemu_monitor_forward_port: int,
) -> Tuple[str, ...]:
    """:returns: the parameters that will always be passed to every instance
    of xqemu that is created
    """
    return (
        (xqemu_binary, "-cpu", "pentium3")
        + (
            "-m",
            ram_size.value,
        )
        + firmware_params
        + (
            "-device",  # Is this the right controller connection code?
            "usb-hub,port=3",
            "-device",
            "usb-xbox-gamepad,port=3.1",
            "-device",
            "lpc47m157",
            "-net",
            "nic,model=nvnet",
            "-net",
            f"user,hostfwd=tcp::{ftp_forward_port}-:21",
            "-serial",
            f"tcp::{kd_forward_port},server",
            "-qmp",
            f"tcp::{qemu_monitor_forward_port},server,nowait",
        )
    )


class XqemuParamTestParams(NamedTuple):
    xqemu_binary: str
    hdd_filename: Optional[str]
    dvd_filename: Optional[str]
    ram_size: XQEMURAMSize
    gloabl_headless: bool
    force_headless: bool


@pytest.mark.parametrize(
    "xqemu_binary,hdd_filename,dvd_filename,ram_size,global_headless,force_headless",
    (
        XqemuParamTestParams("xqemu", None, None, XQEMURAMSize.RAM64m, False, False),
        XqemuParamTestParams(
            "xqemu", "hdd image", None, XQEMURAMSize.RAM64m, False, False
        ),
        XqemuParamTestParams(
            "xqemu", None, "dvd image", XQEMURAMSize.RAM64m, False, False
        ),
        XqemuParamTestParams(
            "xqemu", "hdd image", "dvd image", XQEMURAMSize.RAM64m, False, False
        ),
        XqemuParamTestParams("xqemu", None, None, XQEMURAMSize.RAM64m, False, False),
        XqemuParamTestParams(
            "xqemu", "hdd image 2", None, XQEMURAMSize.RAM64m, False, False
        ),
        XqemuParamTestParams(
            "xqemu", None, "dvd image 2", XQEMURAMSize.RAM64m, False, False
        ),
        XqemuParamTestParams(
            "xqemu", "hdd image 2", "dvd image 2", XQEMURAMSize.RAM64m, False, False
        ),
        XqemuParamTestParams("xqemu", None, None, XQEMURAMSize.RAM128m, False, False),
        XqemuParamTestParams(
            "xqemu", None, "dvd image 2", XQEMURAMSize.RAM64m, False, True
        ),
        XqemuParamTestParams(
            "xqemu", "hdd image 2", "dvd image 2", XQEMURAMSize.RAM64m, True, True
        ),
        XqemuParamTestParams(
            "/bin/someotherbin",
            "hdd image 2",
            "dvd image 2",
            XQEMURAMSize.RAM64m,
            True,
            True,
        ),
    ),
)
def test_xqemu_params(
    mocked_subprocess_popen,
    mocked_unused_port,
    mocked_xqemu_firmware,
    xqemu_binary: str,
    hdd_filename: Optional[str],
    dvd_filename: Optional[str],
    ram_size: XQEMURAMSize,
    global_headless: bool,
    force_headless: bool,
):
    """Ensures that the correct parameters are passed to xqemu"""
    unused_port = mocked_unused_port.return_value
    ports = tuple(random.sample(range(1, 100), 3))
    unused_port.get_port_number.side_effect = ports

    firmware_params = ("test", "firmware")
    mocked_xqemu_firmware.get_command_line_args.return_value = firmware_params

    XQEMUXboxAppRunner._global_params = _XQEMUXboxAppRunnerGlobalParams(
        mocked_xqemu_firmware, global_headless, xqemu_binary=xqemu_binary
    )

    network_forward_rules = None
    with XQEMUXboxAppRunner(
        hdd_filename, dvd_filename, network_forward_rules, ram_size, force_headless
    ) as _:
        pass

    expected_params = get_common_params(xqemu_binary, firmware_params, ram_size, *ports)

    if global_headless or force_headless:
        expected_params += ("-display", "egl-headless")

    if hdd_filename is not None:
        expected_params += ("-drive", f"index=0,media=disk,file={hdd_filename}")
    if dvd_filename is not None:
        expected_params += ("-drive", f"index=1,media=cdrom,file={dvd_filename}")

    mocked_subprocess_popen.assert_called_once_with(expected_params)
