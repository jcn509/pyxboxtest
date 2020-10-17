"""Captures kernel debug (serial port) output from XQEMU"""

import socket

from .._utils import retry_every


class XQEMUKDCapturer:
    """Captures kernel debug (serial port) output from XQEMU"""

    def __init__(self, port: int):
        """:param port: the port on which to listen"""
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        retry_every(lambda: self._client.connect(("", port)))

    def close(self) -> None:
        """Stop listening for serial port output"""
        self._client.close()

    def get_num_chars(self, num_chars: int, encoding: str = "ascii") -> str:
        """Blocks until output is available
        :returns: at most num_chars characters
        """
        return self._client.recv(num_chars).decode(encoding)

    def get_line(self, delim_char="\n", encoding: str = "ascii") -> str:
        """Blocks until output is available
        :returns: entire line (ending with delim_char) of kernel debug output
        """
        # Go character by character so that we don't read too far ahead.
        # However, this method may be slow so the implementation may change in the future...
        chunk_size = 1
        char = self._client.recv(chunk_size).decode(encoding)
        data = char
        while char != delim_char:
            char = self._client.recv(chunk_size).decode(encoding)
            data += char
        return data
