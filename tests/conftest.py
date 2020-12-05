"""Configuration for the tests"""
# pylint: disable=unused-import
import pytest

from pyxboxtest.xqemu.hdd import xqemu_blank_hdd_template

pytest_plugins = ("pyxboxtest.pytest_plugin",)


@pytest.fixture
def mocked_socket(mocker):
    """We don't really want to use a real socket here"""
    mocker.patch("socket.socket.connect")
    mocker.patch("socket.socket.recv")


@pytest.fixture
def mocked_subprocess_popen(mocker):
    """We don't really want to spawn new processes"""
    return mocker.patch("subprocess.Popen")
