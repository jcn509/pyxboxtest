"""Allow an FTP connection to an Xbox app running FTP server within XQEMU"""
from ftplib import FTP

from overrides import overrides

from .._utils import retry_every


class XQEMUFTPClient(FTP):
    """Small wrapper around Python's to deal with an FTP connection that is
    forwarded from XQEMU. Has to set the external IP. For More details please
    read https://bugs.python.org/issue32572 and https://xqemu.com/tips/
    """

    externalip = "10.0.2.2"

    def __init__(self, forwarded_port: int, timeout: int = 60):
        """:param forwarded_port: port that the FTP connection was forwarded to"""
        super().__init__()
        self.set_pasv(False)

        # If the connection is opened too early then it cannot connect
        def try_connect():
            self.connect("127.0.0.1", forwarded_port, timeout)

        retry_every(try_connect)

    @overrides
    def sendport(self, host, port):
        """Send a PORT command with the current host and the given
        port number.

        Host gets overridden, will use externalip instead!
        """
        return super().sendport(self.externalip or host, port)

    @overrides
    def sendeprt(self, host, port):
        """Send an EPRT command with the current host and the given port number.

        Host gets overridden, will use externalip instead!
        """
        return super().sendeprt(self.externalip or host, port)
