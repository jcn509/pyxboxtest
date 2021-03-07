"""Tests for :py:class:`~pyxboxtest.xqemu.XQEMUKDCapturer`"""
from contextlib import contextmanager
from multiprocessing import Process
import socket
from time import sleep
from typing import Iterator, Tuple

import pytest

from pyxboxtest.xqemu import XQEMUKDCapturer
from pyxboxtest._utils import UnusedPort


@pytest.mark.usefixtures("mocked_socket")
@pytest.mark.parametrize("port", tuple(range(4)))
def test_correct_socket(port: int):
    """Very simple test to make sure that the correct socket is set up"""
    XQEMUKDCapturer(port)
    socket.socket.connect.assert_called_with(  # pytype: disable=attribute-error # pylint: disable=no-member
        ("", port)
    )


def run_kd_server(kd_strs: Tuple[str], port: int) -> None:
    """Emulate the socket that xqemu creates for forwarding KD output

    :param kd_strs: the strings that app running in xqemu would send over \
        the serial port
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create socket
    sock.bind(("", port))
    sock.listen(1)  # listening for only one client

    conn, _ = sock.accept()  # accept the connection

    for kd_str in kd_strs:
        conn.send(kd_str.encode())


@contextmanager
def kd_server(kd_strs: Tuple[str], port: int) -> Iterator[Process]:
    """Context manager for a server that sends out the kd_strs in a background
    process. Used to emulate the socket that xqemu creates for forwarding KD
    output.

    :param kd_strs: the strings that app running in xqemu would send over \
        the serial port
    """
    server = Process(target=run_kd_server, args=(kd_strs, port))
    server.start()
    try:
        yield server
    finally:
        server.join()


@contextmanager
def kd_capturer_for_strs(kd_strs: Tuple[str]) -> Iterator[XQEMUKDCapturer]:
    """Context manager for an XQEMUKDCapturer tied to a background server that
    sends out the kd_strs in a background process. Used to emulate the
    socket that xqemu creates for forwarding KD output.

    :param kd_strs: the strings that app running in xqemu would send over \
        the serial port
    """
    port_number = UnusedPort().get_port_number()
    with kd_server(kd_strs, port_number):
        xqemu_kd_capturer = XQEMUKDCapturer(port_number)
        try:
            yield xqemu_kd_capturer
        finally:
            xqemu_kd_capturer.close()


@pytest.mark.parametrize(
    "lines_to_send",
    ("first test\nasdasdasd\n", "second test\nasdasdasd\n", "\ntest\n", "\n\n\n"),
)
def test_get_line_whole_lines_send_from_xqemu(lines_to_send: str):
    """Ensure that we can correctly retrieve any number of lines that have
    been sent if lines are sent in their entirety one at a time
    """
    with kd_capturer_for_strs(lines_to_send) as xqemu_kd_capturer:

        # Drop the final \n
        for line in lines_to_send[:-1].split("\n"):
            assert (
                line + "\n"
            ) == xqemu_kd_capturer.get_line(), "line returned correctly"


@pytest.mark.parametrize(
    "chunks_to_send",
    (
        ("first", "test\n", "asdasdasd\n"),
        ("second test\nasdasdasd", "\n"),
        ("line", "\n"),
        ("l", "i", "n", "e", "\n"),
    ),
)
def test_get_line_partial_lines_send_from_xqemu(chunks_to_send: Tuple[str]):
    """Ensure that we can correctly retrieve any number of lines that have
    been sent if lines are sent in their little chunks
    """
    with kd_capturer_for_strs(chunks_to_send) as xqemu_kd_capturer:

        # Drop the final \n
        for line in "".join(chunks_to_send)[:-1].split("\n"):
            assert (
                line + "\n"
            ) == xqemu_kd_capturer.get_line(), "line returned correctly"


@pytest.mark.parametrize(
    "data_to_send, num_chars_to_receive",
    (("test", 3), ("test", 20), ("test\n\n\asdadasd", 1000), ("test\n\n\asdadasd", 1)),
)
def test_get_num_chars(data_to_send: str, num_chars_to_receive: int):
    """Ensure that we can correctly retrieve at most a certain number of chars"""
    with kd_capturer_for_strs((data_to_send,)) as xqemu_kd_capturer:

        captured_data = xqemu_kd_capturer.get_num_chars(num_chars_to_receive)

        assert len(captured_data) == min(
            len(data_to_send), num_chars_to_receive
        ), "Correct number of characters were captured"
        assert data_to_send.startswith(captured_data)


@pytest.mark.parametrize(
    "data_to_send,", ("test", "test\n\n\asdadasd", "".join("a" for _ in range(10000)),),
)
def test_get_all_data_available(data_to_send: str):
    """Ensure that we can correctly retrieve all data that is currently
    available - assuming that there is some
    """
    with kd_capturer_for_strs((data_to_send,)) as xqemu_kd_capturer:
        # Sleep so that we know the data has been sent before we check
        # as this call does not block
        sleep(1)
        assert (
            xqemu_kd_capturer.get_all() == data_to_send
        ), "we captured all the sent data"


def test_get_all_no_data_available():
    """Ensure that we get an empty string if there is no data available from
    the server and we don't block
    """
    with kd_capturer_for_strs(tuple()) as xqemu_kd_capturer:
        sleep(1)
        assert (
            xqemu_kd_capturer.get_all() == ""
        ), "we did not block and captured something"
