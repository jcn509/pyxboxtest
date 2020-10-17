"""A collection of utility functions requried by pyxboxtest but are not a part of the framework"""
import socket
import time
from typing import Any, Callable, Generator


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


def get_unused_ports(number_of_ports: int) -> Generator[int, None, None]:
    """:returns: a generator for unique and unused ports
    Note: due to the implementation the port will be seen as in use by the OS
    until it is given by the generator
    """

    def get_sock_bind():
        sock = socket.socket()
        sock.bind(("", 0))
        return sock

    def get_port_close(sock):
        port = sock.getsockname()[1]
        sock.close()
        return port

    # Force it to be a tuple, not a generator so that all the ports are in use
    # at once. This will prevent the same port from being returned twice
    sockets = tuple(get_sock_bind() for _ in range(number_of_ports))
    return (get_port_close(s) for s in sockets)
