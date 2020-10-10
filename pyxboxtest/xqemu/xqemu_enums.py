"""Any enum types needed by XQEMU"""
from enum import Enum, unique


@unique
class XQEMURAMSize(Enum):
    RAM64m = "64M"
    RAM128 = "128M"
