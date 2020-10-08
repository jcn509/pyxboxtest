# -*- coding: utf-8 -*-
from contextlib import AbstractContextManager
from ftplib import FTP
import socket
import subprocess
import time

from typing import Any, Callable, Dict, Optional, Union

import qmp


def _retry_every(
    thing_to_try: Callable[[], None], max_retries: int = 100, retry_delay: int = 100
):
    num_tries = 0
    while num_tries < max_retries:
        try:
            thing_to_try()
        except:
            num_tries += 1
            time.sleep(1)
            pass
        else:
            return

    if num_tries == max_retries:
        raise RuntimeError("Attempt failed")


class XQEMUKDCapturer:
    """Captures kernel debug (serial port) output from XQEMU"""

    def __init__(self, socket_addres):
        self._client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        _retry_every(lambda: self._client.connect(socket_addres))

    def close(self) -> None:
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


KD_SOCKET = "/tmp/xserial"
MONITOR_SOCKET = "/tmp/xqemu-monitor-socket"


class XQEMUFTClient(FTP):
    """Small wrapper around Python's to deal with an FTP connection that is
    forwarded from XQEMU. Has to set the external IP. For More details please
    read https://bugs.python.org/issue32572 and https://xqemu.com/tips/
    """

    externalip = "10.0.2.2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_pasv(False)

    def sendport(self, host, port):
        return super().sendport(self.externalip or host, port)

    def sendeprt(self, host, port):
        return super().sendeprt(self.externalip or host, port)


FTP_FORWARD_PORT = 1021


class XboxApp(AbstractContextManager):
    """Run an app in XQEMU with this context manager. The app is killed at the end.
    Provides read/write access to the harddrive, screenshot functionality and the
    ability to send controller input to the console.
    """

    def __init__(
        self,
        hdd_filename: Optional[str] = None,
        dvd_filename: Optional[str] = None,
        headless: bool = False
    ):
        mcpx_rom = "/home/josh/.xqemu_files/mcpx_1.0.bin"
        xqemu_binary = "/bin/xqemu"
        xbox_bios = "/home/josh/.xqemu_files/Complex_4627.bin"

        self._xqemu_args = (
            xqemu_binary,
            "-cpu",
            "pentium3",
            "-machine",
            f"xbox,bootrom={mcpx_rom},short_animation",
            "-m",
            "64M",
            "-bios",
            xbox_bios,
            "-device",
            "usb-xbox-gamepad",
            "-device",
            "lpc47m157",
            "-net",
            "nic,model=nvnet",
            "-net",
            f"user,hostfwd=tcp:127.0.0.1:{FTP_FORWARD_PORT}-:21",
            "-serial",
            f"unix:{KD_SOCKET},server,nowait",
            "-qmp",
            f"unix:{MONITOR_SOCKET},server,nowait",
        )
        if headless:
            self._xqemu_args += ("-display", "egl-headless")

        if hdd_filename is not None:
            self._xqemu_args += ("-drive", f"file={hdd_filename},index=0,media=disk")
        if dvd_filename is not None:
            self._xqemu_args += ("-drive", f"index=1,media=cdrom,file={dvd_filename}")

    def get_ftp_client(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """This assumes that an FTP client is actually running in the app..."""
        ftp_client = XQEMUFTClient()
        ftp_client.connect("127.0.0.1", FTP_FORWARD_PORT, timeout)
        if username is not None and password is not None:
            ftp_client.login(username, password)
        ftp_client.dir()
        return ftp_client

    def press_key(self, key: str, hold_time: Optional[int] = None) -> None:
        # Need to figure out how to set hold time :s
        args: Dict[str, Any] = {"keys": [{"type": "qcode", "data": key}]}
        if hold_time is not None:
            args["hold-time"] = hold_time
        self._qemu_monitor.command("send-key", **args)

    def save_screenshot(self, filename: str) -> None:
        self._qemu_monitor.command("screendump", filename=filename)

    def get_kd_capturer(self) -> Optional[XQEMUKDCapturer]:
        return self._kd_capturer

    def get_app_sub_process(self):
        return self._app

    def __enter__(self):
        self._app = subprocess.Popen(self._xqemu_args)
        self._qemu_monitor = qmp.QEMUMonitorProtocol(MONITOR_SOCKET)
        self._kd_capturer = XQEMUKDCapturer(KD_SOCKET)
        _retry_every(lambda: self._qemu_monitor.connect())
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._qemu_monitor.close()
        self._qemu_monitor = None
        self._kd_capturer.close()
        self._kd_capturer = None
        self._app.kill()
        self._app = None


import pytest


@pytest.fixture
def nevolutionx_app():
    with XboxApp(
        hdd_filename="/home/josh/.xqemu_files/xbox_hdd.qcow2",
        dvd_filename="/home/josh/Downloads/NevolutionX.iso",
    ) as app:
        yield app


@pytest.fixture
def nevolutionx_ftp_client(nevolutionx_app):
    return nevolutionx_app.get_ftp_client("xbox", "xbox")


def test_nevolutionx_ftp(nevolutionx_ftp_client):
    nevolutionx_ftp_client.dir()

def test_usb_code():
    with XboxApp(
        hdd_filename="/home/josh/.xqemu_files/xbox_hdd.qcow2",
        dvd_filename="/home/josh/projects/ind_revived_os/hello.iso",
        headless=True,
    ) as app:
        print("gonna try for some output now")
        kd = app.get_kd_capturer()
        nothing_pressed = kd.get_line()
        a_key_text = '"keys":"A"'
        assert a_key_text not in nothing_pressed, "A not pressed"

        app.press_key("s", hold_time=50)
        a_pressed = kd.get_line()
        print(a_pressed, a_key_text in a_pressed)
        assert a_key_text in a_pressed, "A not pressed"

        a_released = kd.get_line()
        assert a_key_text not in a_released, "A not pressed"
