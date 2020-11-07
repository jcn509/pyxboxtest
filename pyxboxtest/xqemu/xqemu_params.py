"""Any types needed by XQEMU to specify its parameters"""
from dataclasses import dataclass
from enum import Enum, unique
import re
from typing import Optional

_IP_REGEX = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def _validate_ip_address(ip_address: Optional[str]) -> None:
    """:raises ValueError: if the IP is not blank or does not have the\
        correct format
    """
    if ip_address and not _IP_REGEX.match(ip_address):
        raise ValueError("Invalid IP address")


def _validate_port(port: int) -> None:
    """:raises ValueError: port number is outside the allowed range"""
    if not 0 <= port <= 65535:
        raise ValueError("Port number must be in range [0, 65535]")


@unique
class NetworkTransportProtocol(Enum):
    """Network layer 4 transport protocol"""

    TCP = "tcp"
    UDP = "udp"


@unique
class XQEMURAMSize(Enum):
    """How much RAM is available to the Xbox"""

    RAM64m = "64M"
    RAM128 = "128M"


def _ip_str(ip_address: Optional[str]) -> str:
    return "" if ip_address is None else ip_address


@dataclass(frozen=True)
class XQEMUNetworkForwardRule:
    """Describe how network connections should be forwarded
    "from" the Xbox app "to" somewhere else.
    """

    xbox_port: int
    forward_to_port: int
    transport_protocol: NetworkTransportProtocol = NetworkTransportProtocol.TCP
    xbox_ip: Optional[str] = None
    forward_to_ip: Optional[str] = None

    def __post_init__(self):
        """Validate the IPs and port"""
        _validate_ip_address(self.xbox_ip)
        _validate_ip_address(self.forward_to_ip)

        _validate_port(self.xbox_port)
        _validate_port(self.forward_to_port)

    def get_rule_str(self) -> str:
        """:returns: a string that can be given to XQEMU to do the network
        forwarding
        """
        return (
            f"user,hostfwd={self.transport_protocol.value}:"
            f"{_ip_str(self.forward_to_ip)}:{self.forward_to_port}-"
            f"{_ip_str(self.xbox_ip)}:{self.xbox_port}"
        )
