from ftplib import FTP

from .._utils import retry_every


class XQEMUFTPClient(FTP):
    """Small wrapper around Python's to deal with an FTP connection that is
    forwarded from XQEMU. Has to set the external IP. For More details please
    read https://bugs.python.org/issue32572 and https://xqemu.com/tips/
    """

    externalip = "10.0.2.2"

    def __init__(self, forwarded_port: int, timeout: int = 60):
        super().__init__()
        self.set_pasv(False)

        # If the connection is opened too early then it cannot connect
        def try_connect():
            self.connect("127.0.0.1", forwarded_port, timeout)

        retry_every(try_connect)

    def sendport(self, host, port):
        return super().sendport(self.externalip or host, port)

    def sendeprt(self, host, port):
        return super().sendeprt(self.externalip or host, port)
