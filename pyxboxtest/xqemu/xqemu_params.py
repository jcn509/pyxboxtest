"""Any enum types needed by XQEMU to specify its parameters"""
from enum import Enum, unique


@unique
class XQEMURAMSize(Enum):
    """How much ram is available to the Xbox"""

    RAM64m = "64M"
    RAM128 = "128M"
