"""Tests for :py:class:`~pyxboxtest.xqemu.XQEMUKDCapturer`"""
import socket

import pytest

from pyxboxtest.xqemu import XQEMUKDCapturer


@pytest.fixture(scope="function", autouse=True)
def mocked_socket(mocker):
    """We don't really want to use a real socket here"""
    mocker.patch("socket.socket.connect")
    mocker.patch("socket.socket.recv")


@pytest.mark.parametrize("port", tuple(range(4)))
def test_correct_socket(port):
    """Very simple test to make sure that the correct socket is set up"""
    XQEMUKDCapturer(port)
    socket.socket.connect.assert_called_with(("", port))


@pytest.mark.parametrize(
    "lines_to_send",
    ("first test\nasdasdasd\n", "second test\nasdasdasd\n", "\ntest\n", "\n\n\n"),
)
def test_get_line(lines_to_send):
    """Ensure that we can correctly retrieve any number of lines that have been sent"""
    string_it = (byte for byte in bytes(lines_to_send, "ascii"))
    socket.socket.recv.side_effect = lambda n: bytes(next(string_it) for x in range(n))

    xqemu_kd_capturer = XQEMUKDCapturer(0)

    # Drop the final \n
    for line in lines_to_send[:-1].split("\n"):
        assert (line + "\n") == xqemu_kd_capturer.get_line(), "line returned correctly"
