"""Tests for :py:class:`~pyxboxtest.xqemu.XQEMUXboxAppRunner`"""
import pytest

from pyxboxtest.xqemu import XQEMUXboxAppRunner

COMMON_XQEMU_PARAMS = (
    "xqemu",
    "-cpu",
    "pentium3",
    "-machine",
    "xbox,bootrom=dontcare,short_animation",
    "-m",
    "64M",
    "-bios",
    "dontcare",
    "-device",
    "usb-xbox-gamepad",
    "-device",
    "lpc47m157",
    "-net",
    "nic,model=nvnet",
    "-net",
    "user,hostfwd=tcp:127.0.0.1:51627-:21",
    "-serial",
    "tcp::52451,server,nowait",
    "-qmp",
    "tcp::55047,server,nowait",
)


def test_xqemu_params(mocked_subprocess_popen):
    """Ensures that the correct parameters are bassed to xqemu"""
    with XQEMUXboxAppRunner() as _:
        pass
    mocked_subprocess_popen.assert_called_once_with(())
