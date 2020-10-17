# -*- coding: utf-8 -*-
from pyxboxtest.xqemu import XQEMUXboxAppRunner, XQEMUXboxControllerButtons
from pyxboxtest.xqemu.hdd import XQEMUHDDTemplate

import pytest


@pytest.fixture
def nevolutionx_app(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    with XQEMUXboxAppRunner(
        hdd_filename=xqemu_blank_hdd_template.create_fresh_hdd(),
        dvd_filename="/home/josh/Downloads/NevolutionX.iso",
    ) as app:
        yield app


@pytest.fixture
def nevolutionx_ftp_client(nevolutionx_app):
    return nevolutionx_app.get_ftp_client("xbox", "xbox")


def test_nevolutionx_ftp(nevolutionx_ftp_client):
    nevolutionx_ftp_client.dir()


def test_usb_code(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    with XQEMUXboxAppRunner(
        hdd_filename=xqemu_blank_hdd_template.create_fresh_hdd(),
        dvd_filename="/home/josh/projects/ind_revived_os/hello.iso",
    ) as app:
        print("gonna try for some output now")
        kd = app.get_kd_capturer()
        nothing_pressed = kd.get_line()
        a_key_text = '"keys":"A"'
        assert a_key_text not in nothing_pressed, "A not pressed"

        app.press_keys((XQEMUXboxControllerButtons.A,), hold_time=50)
        a_pressed = kd.get_line()
        print(a_pressed, a_key_text in a_pressed)
        assert a_key_text in a_pressed, "A not pressed"

        a_released = kd.get_line()
        assert a_key_text not in a_released, "A not pressed"
