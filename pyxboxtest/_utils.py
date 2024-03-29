"""A collection of utility functions required by pyxboxtest but are not a part of the framework"""
from ftplib import FTP
import re
import socket
import time
from typing import Any, Callable, Set


def validate_xbox_file_path(path: str) -> None:
    """:raises IOError: if the path is not of the correct form"""
    if not re.match(r"^/[CDEFGXYZ]/.*[^/]$", path):
        raise IOError(
            f"Path {path} must be of the form\
            /<Drive letter/<path> e.g. /C/test/file.txt"
        )


def validate_xbox_directory_path(path: str) -> None:
    """:raises IOError: if the path is not of the correct form"""
    if not re.match(r"^/[CDEFGXYZ]/($|(.+/$))", path):
        raise IOError(
            f"Path {path} must be of the form\
            /<Drive letter/<path>/ e.g. /C/test/"
        )


def remove_ftp_dir(ftp: FTP, path: str) -> None:
    """Deletes a directories contents (recursively) before then deletes the
    directory itself
    """
    path = path.rstrip("/")
    lines = []
    ftp.retrlines(f"LIST {path}/", lines.append)

    for line in lines:
        components = line.split(" ")
        name = " ".join(components[7:])
        is_dir = components[0][0] == "d"

        if name in [".", ".."]:
            continue
        elif not is_dir:
            ftp.delete(f"{path}/{name}")
        else:
            remove_ftp_dir(ftp, f"{path}/{name}")

    ftp.rmd(path)


def retry_every(
    thing_to_try: Callable[[], Any],
    max_tries: int = 300,
    delay_before_retry: float = 0.05,
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

    def get_port_number(self) -> int:
        """The number of the port"""
        # Release control of the port so that it can be used
        if self._sock is not None:
            self._sock.close()
        self._sock = None
        return self._port_number
