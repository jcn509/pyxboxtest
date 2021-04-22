"""Tests for :py:class:`~pyxboxtest.xqemu.XQEMUXboxAppRunner`"""
import os
import random
from typing import Any, Dict, NamedTuple, Optional, Sequence, Tuple

import pytest

from pyxboxtest.xqemu import (
    XQEMURAMSize,
    XQEMUXboxAppRunner,
    XQEMUXboxControllerButtons,
)
from pyxboxtest.xqemu.xqemu_xbox_app_runner import _XQEMUXboxAppRunnerGlobalParams
from pyxboxtest.xqemu._xqemu_temporary_directories import get_temp_dirs

_XQEMU_DEFAULT_BINARY = "xqemu"


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


@pytest.fixture
def mocked_qemu_monitor(mocker):
    """mock :py:class:`~qmp.QEMUMonitorProtocol` so that we can check it is
    used correctly
    """
    return mocker.patch("pyxboxtest.xqemu.xqemu_xbox_app_runner.QEMUMonitorProtocol")


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
        + ("-m", ram_size.value,)
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
    """All the data needed to test the parameters passed to xqemu.

    This class exists for type checking purposes only
    """

    xqemu_binary: str
    hdd_filename: Optional[str]
    dvd_filename: Optional[str]
    ram_size: XQEMURAMSize
    gloabl_headless: bool
    force_headless: bool
    firmware_params: Tuple[str, ...]


@pytest.mark.parametrize(
    "xqemu_binary,hdd_filename,dvd_filename,ram_size,global_headless,force_headless,firmware_params",
    (
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            None,
            None,
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            "hdd image",
            None,
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            None,
            "dvd image",
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            "hdd image",
            "dvd image",
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("one", "two"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            None,
            None,
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            "hdd image 2",
            None,
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            None,
            "dvd image 2",
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            "hdd image 2",
            "dvd image 2",
            XQEMURAMSize.RAM64m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            None,
            None,
            XQEMURAMSize.RAM128m,
            False,
            False,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            None,
            "dvd image 2",
            XQEMURAMSize.RAM64m,
            False,
            True,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            _XQEMU_DEFAULT_BINARY,
            "hdd image 2",
            "dvd image 2",
            XQEMURAMSize.RAM64m,
            True,
            True,
            ("test", "firmware"),
        ),
        XqemuParamTestParams(
            "/bin/someotherbin",
            "hdd image 2",
            "dvd image 2",
            XQEMURAMSize.RAM64m,
            True,
            True,
            ("test", "firmware"),
        ),
    ),
)
def xqemu_params_for_test(
    mocked_subprocess_popen,
    mocked_unused_port,
    mocked_xqemu_firmware,
    xqemu_binary: str,
    hdd_filename: Optional[str],
    dvd_filename: Optional[str],
    ram_size: XQEMURAMSize,
    global_headless: bool,
    force_headless: bool,
    firmware_params: Tuple[str, ...],
):
    """Ensures that the correct parameters are passed to xqemu"""
    unused_port = mocked_unused_port.return_value
    ports = tuple(random.sample(range(1, 100), 3))
    unused_port.get_port_number.side_effect = ports

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


def get_qmp_port_from_xqemu_params(xqemu_params: Tuple[str, ...]) -> int:
    """Extract that port used by the QEMU monitor from the paramters passed to
    xqemu
    """
    previous_param = xqemu_params[0]
    for param in xqemu_params[1:]:
        if previous_param == "-qmp":
            return int(param.split("::")[1].split(",")[0])
        previous_param = param

    raise ValueError("Could not find -qmp switch")


def get_kd_capturer_port_from_xqemu_params(xqemu_params: Tuple[str, ...]) -> int:
    """Extract that port used by the KD capturer from the paramters passed to
    xqemu
    """
    previous_param = xqemu_params[0]
    for param in xqemu_params[1:]:
        if previous_param == "-serial":
            return int(param.split("::")[1].split(",")[0])
        previous_param = param

    raise ValueError("Could not find -serial switch")


class AppRunnerWithParams(XQEMUXboxAppRunner):
    """An extension of :py:class:`~pyxboxtest.xqemu.XQEMUXboxAppRunner`
    provides access to the parameters given to xqemu via the property
    xqemu_params_for_test
    """

    def __init__(self, mocked_subprocess_popen, *args, **kwargs):
        """:param mocked_subprocess_popen: used to ensure that XQEMU is not
        really called and to capture the params that would be given to it
        """
        super().__init__(*args, **kwargs)
        self._mocked_subprocess_popen = mocked_subprocess_popen
        self.xqemu_params_for_test = tuple()

    def __enter__(self):
        ret = super().__enter__()
        # Arg 0 is the tuple of parameters
        self.xqemu_params_for_test = self._mocked_subprocess_popen.call_args.args[0]
        return ret


@pytest.fixture
def default_xqemu_xbox_app_runner(
    mocked_unused_port, mocked_xqemu_firmware, mocked_subprocess_popen
):
    """Get a basic :py:class:`~pyxboxtest.xqemu.XQEMUXboxAppRunner` along with
    the parameters that were passed to xqemu. The ports used are random.
    The parameters are stored in the property xqemu_params_for_test
    """
    mocked_xqemu_firmware.get_command_line_args.return_value = ("", "")

    unused_port = mocked_unused_port.return_value
    ports = tuple(random.sample(range(1, 100), 3))
    unused_port.get_port_number.side_effect = ports

    XQEMUXboxAppRunner._global_params = _XQEMUXboxAppRunnerGlobalParams(
        mocked_xqemu_firmware, True
    )

    with AppRunnerWithParams(mocked_subprocess_popen) as app_runner:
        yield app_runner


def test_get_qemu_monitor(
    default_xqemu_xbox_app_runner: AppRunnerWithParams, mocked_qemu_monitor
):
    """Ensures that the qemu monitor is created using the right parameters"""
    qmp_monitor_port = get_qmp_port_from_xqemu_params(
        default_xqemu_xbox_app_runner.xqemu_params_for_test
    )
    default_xqemu_xbox_app_runner.get_qemu_monitor()
    mocked_qemu_monitor.assert_called_once_with(("", qmp_monitor_port))


def test_kd_capturer(
    default_xqemu_xbox_app_runner: AppRunnerWithParams, mocked_kd_capturer
):
    """Ensures that :py:class:`~pyxboxtest.xqemu.XQEMUKDCapturer` is created
    using the right parameters
    """
    kd_capturer_port = get_kd_capturer_port_from_xqemu_params(
        default_xqemu_xbox_app_runner.xqemu_params_for_test
    )
    mocked_kd_capturer.assert_called_once_with(kd_capturer_port)


class PressControllerButtonsParams(NamedTuple):
    """All the inputs needed to test pressing controller buttons

    This class exists for type checking purposes only
    """

    buttons_to_press: Sequence[XQEMUXboxControllerButtons]
    hold_time: Optional[int]
    send_key_arguments: Dict[str, Any]


@pytest.mark.usefixtures("mocked_qemu_monitor")
@pytest.mark.parametrize(
    "buttons_to_press,hold_time,send_key_arguments",
    (
        PressControllerButtonsParams(
            (XQEMUXboxControllerButtons.A,),
            None,
            {"keys": [{"type": "qcode", "data": XQEMUXboxControllerButtons.A.value}]},
        ),
        PressControllerButtonsParams(
            (XQEMUXboxControllerButtons.B, XQEMUXboxControllerButtons.DPAD_DOWN),
            None,
            {
                "keys": [
                    {"type": "qcode", "data": XQEMUXboxControllerButtons.B.value},
                    {
                        "type": "qcode",
                        "data": XQEMUXboxControllerButtons.DPAD_DOWN.value,
                    },
                ]
            },
        ),
        PressControllerButtonsParams(
            (XQEMUXboxControllerButtons.X,),
            10,
            {
                "keys": [
                    {"type": "qcode", "data": XQEMUXboxControllerButtons.X.value},
                ],
                "hold-time": 10,
            },
        ),
        PressControllerButtonsParams(
            (
                XQEMUXboxControllerButtons.RIGHT_THUMB_DOWN,
                XQEMUXboxControllerButtons.LEFT_THUMB_LEFT,
            ),
            43,
            {
                "keys": [
                    {
                        "type": "qcode",
                        "data": XQEMUXboxControllerButtons.RIGHT_THUMB_DOWN.value,
                    },
                    {
                        "type": "qcode",
                        "data": XQEMUXboxControllerButtons.LEFT_THUMB_LEFT.value,
                    },
                ],
                "hold-time": 43,
            },
        ),
    ),
)
def test_press_controller_buttons(
    buttons_to_press: Sequence[XQEMUXboxControllerButtons],
    hold_time: Optional[int],
    default_xqemu_xbox_app_runner: AppRunnerWithParams,
    send_key_arguments: Dict[str, Any],
):
    """Ensures that the qemu monitor is used correctly to send controller
    input to XQEMU
    """
    qemu_monitor = default_xqemu_xbox_app_runner.get_qemu_monitor()
    default_xqemu_xbox_app_runner.press_controller_buttons(
        buttons_to_press, hold_time=hold_time
    )
    qemu_monitor.command.assert_called_once_with("send-key", **send_key_arguments)


@pytest.mark.parametrize(
    "invalid_screenshot_filename",
    ("incorrect.extension", "noextension", "file.jpg", "file.png"),
)
def test_save_screenshot_invalid_extension(
    default_xqemu_xbox_app_runner: AppRunnerWithParams, invalid_screenshot_filename: str
):
    """Ensures that exceptions are thrown if a screenshots filename extension
    is invalid. Only the .ppm extension is allowed
    """
    with pytest.raises(ValueError):
        default_xqemu_xbox_app_runner.save_screenshot(invalid_screenshot_filename)


@pytest.mark.parametrize(
    "invalid_screenshot_filename",
    ("somedir\\incorrect.ppm", "dir/file.ppm", os.path.join("test", "test.ppm")),
)
def test_save_screenshot_filename_contains_path(
    default_xqemu_xbox_app_runner: AppRunnerWithParams, invalid_screenshot_filename: str
):
    """Ensures that exceptions are thrown if a screenshots filename contains
    the path to a directory e.g. dir/test.ppm
    """
    with pytest.raises(ValueError):
        default_xqemu_xbox_app_runner.save_screenshot(invalid_screenshot_filename)


@pytest.mark.usefixtures("mocked_qemu_monitor")
@pytest.mark.parametrize(
    "screenshot_filenames,first_screenshot_number",
    (
        (("screenshot.ppm",), 1),
        # Start saving screenshots with number 2 as we saved 1 in the previous
        # test
        (("file.ppm", "otherfile.ppm"), 2),
    ),
)
def test_save_screenshot_correct_paths(
    default_xqemu_xbox_app_runner: AppRunnerWithParams,
    screenshot_filenames: Tuple[str],
    first_screenshot_number: int,
):
    """Ensure that a screenshot is stored in the temporary directory and that
    each one is numbered to make sure that they are unique
    """
    qemu_monitor = default_xqemu_xbox_app_runner.get_qemu_monitor()
    for screenshot_number, screenshot_filename in enumerate(
        screenshot_filenames, first_screenshot_number
    ):
        default_xqemu_xbox_app_runner.save_screenshot(screenshot_filename)
        screenshot_path = os.path.join(
            get_temp_dirs().screenshots_dir,
            str(screenshot_number) + "-" + screenshot_filename,
        )
        qemu_monitor.command.assert_called_with("screendump", filename=screenshot_path)
