# -*- coding: utf-8 -*-
from ftplib import FTP
import json
from time import sleep
from typing import Any, Dict, Iterator, NamedTuple, Tuple

from pyxboxtest.xqemu import (
    XQEMUKDCapturer,
    XQEMUXboxAppRunner,
    XQEMUXboxControllerButtons,
)
from pyxboxtest.xqemu.hdd import XQEMUHDDTemplate

import dpath.util
import pytest


@pytest.fixture
def nevolutionx_app(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    with XQEMUXboxAppRunner(
        hdd_filename=xqemu_blank_hdd_template.create_fresh_hdd(),
        dvd_filename="/home/josh/Downloads/NevolutionX.iso",
    ) as app:
        yield app


@pytest.fixture
def nevolutionx_ftp_client(nevolutionx_app: XQEMUXboxAppRunner) -> FTP:
    return nevolutionx_app.get_ftp_client("xbox", "xbox")


def test_nevolutionx_ftp(nevolutionx_ftp_client: FTP):
    nevolutionx_ftp_client.dir()


def test_kernel_debug(xqemu_blank_hdd_template):
    with XQEMUXboxAppRunner(
        hdd_filename=xqemu_blank_hdd_template.create_fresh_hdd(),
        dvd_filename="/home/josh/projects/nxdk/samples/kernel_debug/kernel_debug.iso",
    ) as app:
        kd = app.get_kd_capturer()
        for count in range(1, 10):
            assert kd.get_line() == f"Hello world! Output count: {count}\n"


def kd_get_json(kd_capturer: XQEMUKDCapturer) -> Dict[str, Any]:
    """Gets the next available KD line and converts it from JSON to a dict"""
    return json.loads(kd_capturer.get_line())


def get_default_buttons_dict() -> Dict[str, Dict[str, Any]]:
    return {
        "Axis": {
            "Lstick": {"x": 0, "y": -1},
            "Rstick": {"x": 0, "y": -1},  # Not sure why y is -1 by default...
            "Ltrig": 0,
            "Rtrig": 0,
        },
        "Buttons": {
            "A": 0,
            "B": 0,
            "X": 0,
            "Y": 0,
            "Back": 0,
            "Start": 0,
            "White": 0,
            "Black": 0,
            "Up": 0,
            "Down": 0,
            "Left": 0,
            "Right": 0,
            "Lstick": 0,
            "Rstick": 0,
        },
    }


def get_buttons_dict(
    buttons_pressed: Tuple[XQEMUXboxControllerButtons, ...]
) -> Dict[str, Dict[str, Any]]:
    buttons_dict = get_default_buttons_dict()

    axis = "Axis"
    buttons = "Buttons"

    class ButtonPathMapping(NamedTuple):
        path: str
        value: int = 1

    axis_min = -32768
    axis_max = 32767
    button_mapping: Dict[XQEMUXboxControllerButtons, ButtonPathMapping] = {
        # Triggers
        XQEMUXboxControllerButtons.LEFT_TRIGGER: ButtonPathMapping(
            f"{axis}/Ltrig", axis_max
        ),
        XQEMUXboxControllerButtons.RIGHT_TRIGGER: ButtonPathMapping(
            f"{axis}/Rtrig", axis_max
        ),
        # Left thumbstick
        XQEMUXboxControllerButtons.LEFT_THUMB_UP: ButtonPathMapping(
            f"{axis}/Lstick/y", axis_min
        ),
        XQEMUXboxControllerButtons.LEFT_THUMB_DOWN: ButtonPathMapping(
            f"{axis}/Lstick/y", axis_max
        ),
        XQEMUXboxControllerButtons.LEFT_THUMB_LEFT: ButtonPathMapping(
            f"{axis}/Lstick/x", axis_min
        ),
        XQEMUXboxControllerButtons.LEFT_THUMB_RIGHT: ButtonPathMapping(
            f"{axis}/Lstick/x", axis_max
        ),
        XQEMUXboxControllerButtons.LEFT_THUMB_PRESS: ButtonPathMapping(
            f"{buttons}/Lstick"
        ),
        # Right thumbstick
        XQEMUXboxControllerButtons.RIGHT_THUMB_UP: ButtonPathMapping(
            f"{axis}/Rstick/y", axis_min
        ),
        XQEMUXboxControllerButtons.RIGHT_THUMB_DOWN: ButtonPathMapping(
            f"{axis}/Rstick/y", axis_max
        ),
        XQEMUXboxControllerButtons.RIGHT_THUMB_LEFT: ButtonPathMapping(
            f"{axis}/Rstick/x", axis_min
        ),
        XQEMUXboxControllerButtons.RIGHT_THUMB_RIGHT: ButtonPathMapping(
            f"{axis}/Rstick/x", axis_max
        ),
        XQEMUXboxControllerButtons.RIGHT_THUMB_PRESS: ButtonPathMapping(
            f"{buttons}/Rstick"
        ),
        # Face buttons
        XQEMUXboxControllerButtons.A: ButtonPathMapping(f"{buttons}/A"),
        XQEMUXboxControllerButtons.B: ButtonPathMapping(f"{buttons}/B"),
        XQEMUXboxControllerButtons.X: ButtonPathMapping(f"{buttons}/X"),
        XQEMUXboxControllerButtons.Y: ButtonPathMapping(f"{buttons}/Y"),
        # White and black
        XQEMUXboxControllerButtons.WHITE: ButtonPathMapping(f"{buttons}/White"),
        XQEMUXboxControllerButtons.BLACK: ButtonPathMapping(f"{buttons}/Black"),
        # Start and back
        XQEMUXboxControllerButtons.START: ButtonPathMapping(f"{buttons}/Start"),
        XQEMUXboxControllerButtons.BACK: ButtonPathMapping(f"{buttons}/Back"),
        # DPAD
        XQEMUXboxControllerButtons.DPAD_UP: ButtonPathMapping(f"{buttons}/Up"),
        XQEMUXboxControllerButtons.DPAD_DOWN: ButtonPathMapping(f"{buttons}/Down"),
        XQEMUXboxControllerButtons.DPAD_LEFT: ButtonPathMapping(f"{buttons}/Left"),
        XQEMUXboxControllerButtons.DPAD_RIGHT: ButtonPathMapping(f"{buttons}/Right"),
    }

    for button in buttons_pressed:
        path, value = button_mapping[button]
        print("setting ")
        dpath.util.set(buttons_dict, path, value)

    return buttons_dict


@pytest.mark.parametrize(
    "buttons_pressed",
    tuple((button,) for button in XQEMUXboxControllerButtons)
    # + ((XQEMUXboxControllerButtons.A, XQEMUXboxControllerButtons.B),),
)
def test_usb_code(
    xqemu_blank_hdd_template: XQEMUHDDTemplate,
    buttons_pressed: Tuple[XQEMUXboxControllerButtons, ...],
):
    with XQEMUXboxAppRunner(
        hdd_filename=xqemu_blank_hdd_template.create_fresh_hdd(),
        dvd_filename="/home/josh/projects/nxdk/samples/sdl_gamecontroller/sdl_gamecontroller.iso",
    ) as app:
        kd = app.get_kd_capturer()
        kd.get_line()
        kd.get_line()

        assert (
            kd_get_json(kd) == get_default_buttons_dict()
        ), "No buttons pressed initially"

        app.press_controller_buttons(buttons_pressed, hold_time=150)
        assert kd_get_json(kd) == get_buttons_dict(buttons_pressed), "Buttons pressed"

        sleep(0.3)  # Give the Xbox time to register that the button has been released
        assert kd_get_json(kd) == get_default_buttons_dict(), "Buttons released"
