# -*- coding: utf-8 -*-
import socket
import os

import subprocess
import time

from typing import Optional

import qmp

KD_SOCKET = "/tmp/xserial"

def _connect_to_sock(socket_name: str, max_retries: int = 100, retry_delay: int = 100):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    attempts = 0
    max_attempts = 100
    while attempts < max_attempts:
        try:
            client.connect(socket_name)
        except:
            attempts += 1
            time.sleep(1)
            pass
        else:
            print("connected", socket_name)
            return client

    if attempts == max_attempts:
        raise Exception("fail lol")





class KDCapture:
    def __init__(self):
        self._client = _connect_to_sock(KD_SOCKET)
        
    def get_line(self, max_size = 1, delim="\n"):
        char = self._client.recv(max_size).decode('ascii')
        data = char 
        while char != delim:
            char = self._client.recv(max_size).decode('ascii')
            data+=char
        return data
    # Do  need to disconnect in destructor or is that done for me anyway?


MONITOR_SOCKET = "/tmp/xqemu-monitor-socket"
class XQEMUMonitor:
    def __init__(self):
        self._client = qmp.QEMUMonitorProtocol(MONITOR_SOCKET)
        
        attempts = 0
        max_attempts = 10
        while attempts < max_attempts:
            try:
                self._client.connect()
            except:
                attempts += 1
                time.sleep(1)
                print("faile")
            else:
                print("connected", MONITOR_SOCKET)
                break

    def press_key(self, key: str, hold_time: Optional[int] = None):
        # Need to figure out how to set hold time :s
        args = {
            "keys": [
                { "type": "qcode", "data": key }
            ]
        }
        if hold_time is not None:
            args["hold-time"] = hold_time
        self._client.command("send-key", **args)

    def save_screenshot(self, filename: str):
        self._client.command("screendump", filename = filename, )

def run_app():
    # May want to force waiting for KD/Monitor, but doing so is annoying if using both...
    # could perhaps just force wait on one of them?
    return subprocess.Popen(["/bin/xqemu", "-cpu", "pentium3", "-machine", "xbox,bootrom=/home/josh/.xqemu_files/mcpx_1.0.bin,short_animation", "-m", "64M", "-bios", "/home/josh/.xqemu_files/Complex_4627.bin", "-drive", "file=/home/josh/.xqemu_files/xbox_hdd.qcow2,index=0,media=disk", "-drive", "index=1,media=cdrom,file=/home/josh/projects/ind_revived_os/hello.iso", "-device", "usb-xbox-gamepad", "-device", "lpc47m157", "-serial", "unix:" + KD_SOCKET +",server,nowait", "-qmp", "unix:" + MONITOR_SOCKET + ",server,nowait", "-display", "egl-headless"],
    stdin=subprocess.PIPE
            )

def test_usb_code():
    app = run_app()
    monitor = XQEMUMonitor()
    kd = KDCapture()
    print("gonna try for some output now")

    nothing_pressed = kd.get_line()
    a_key_text = '"keys":"A"'
    assert a_key_text not in nothing_pressed, "A not pressed"

    monitor.press_key("s", hold_time=50)
    a_pressed = kd.get_line()
    print(a_pressed, a_key_text in a_pressed)
    assert a_key_text in a_pressed, "A not pressed"

    a_released = kd.get_line()
    assert a_key_text not in a_released, "A not pressed"

    app.kill()
