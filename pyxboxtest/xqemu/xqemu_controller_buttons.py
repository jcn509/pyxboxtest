"""Mapping from Xbox controller buttons/joysticks to the values used by XQEMU"""
from enum import Enum, unique


@unique
class XQEMUXboxControllerButtons(Enum):
    """Mapping from Xbox controller buttons/joysticks to the values used by XQEMU"""

    # Face buttons
    A = "s"
    B = "d"
    X = "w"
    Y = "e"

    # White and black
    WHITE = "x"
    BLACK = "c"

    # Start and back
    START = "ret"
    BACK = "backspace"

    # DPAD
    DPAD_UP = "up"
    DPAD_DOWN = "down"
    DPAD_LEFT = "left"
    DPAD_RIGHT = "right"

    # Triggers
    LEFT_TRIGGER = "q"
    RIGHT_TRIGGER = "r"

    # Left thumbstick
    LEFT_THUMB_UP = "t"
    LEFT_THUMB_DOWN = "g"
    LEFT_THUMB_LEFT = "f"
    LEFT_THUMB_RIGHT = "h"
    LEFT_THUMB_PRESS = "v"

    # Right thumbstick
    RIGHT_THUMB_UP = "i"
    RIGHT_THUMB_DOWN = "k"
    RIGHT_THUMB_LEFT = "j"
    RIGHT_THUMB_RIGHT = "l"
    RIGHT_THUMB_PRESS = "m"
