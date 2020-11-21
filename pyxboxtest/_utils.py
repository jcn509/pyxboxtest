"""A collection of utility functions requried by pyxboxtest but are not a part of the framework"""
import socket
import time
from typing import Any, Callable, Set

from cached_property import cached_property


def retry_every(
    thing_to_try: Callable[[], Any], max_tries: int = 15, delay_before_retry: int = 1
):
    """Keep trying something that may throw an exception
    :returns: whatever thing_to_try returns
    :throws: whatever thing_to_try throws on the last try
    """
    if max_tries <= 0:
        raise ValueError("Cannot try something less than 1 time...")
    num_tries = 0
    while True:
        try:
            return thing_to_try()
        except:
            num_tries += 1
            if num_tries == max_tries:
                raise
            time.sleep(delay_before_retry)


class UnusedPort:
    """Used to obtain a unique port that is not in use by the OS or
    "reserved for use" in this app

    Once a port has been reserved by instantiating an object of this class it
    will not be given again until after the object is destroyed
    """

    _reserved_ports: Set[int] = set()

    def __init__(self):
        unused_socks = []
        sock = socket.socket()
        sock.bind(("", 0))

        # Make sure that we are not using a port that has already
        # been marked as in use!
        # Keep the "bound sock" around so that OS won't just
        # keep allocating us the same socket though
        while sock.getsockname()[1] in UnusedPort._reserved_ports:
            unused_socks.append(sock)
            sock = socket.socket()
            sock.bind(("", 0))
        for unused_sock in unused_socks:
            unused_sock.close()

        self._sock = sock

        self._port_number = sock.getsockname()[1]
        UnusedPort._reserved_ports.add(self._port_number)

    def __del__(self):
        UnusedPort._reserved_ports.remove(self._port_number)

    @cached_property  # Don't want to close the socket more than once!
    def port_number(self) -> int:
        """The number of the port"""
        # Release control of the port so that it can be used
        self._sock.close()
        return self._port_number
