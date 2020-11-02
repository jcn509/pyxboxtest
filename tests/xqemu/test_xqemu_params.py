"""Tests for :py:class:`~pyxboxtest.xqemu.xqemu_params`"""
import pytest

from pyxboxtest.xqemu import NetworkTransportProtocol, XQEMUNetworkForwardRule


@pytest.mark.parametrize(
    "network_forward_rule, expected_str",
    (
        (XQEMUNetworkForwardRule(21, 44), "user,hostfwd=tcp::44-:21"),
        (
            XQEMUNetworkForwardRule(21, 44, NetworkTransportProtocol.UDP),
            "user,hostfwd=udp::44-:21",
        ),
        (
            XQEMUNetworkForwardRule(
                500, 22, xbox_ip="100.101.120.9", forward_to_ip="12.34.56.78"
            ),
            "user,hostfwd=tcp:12.34.56.78:22-100.101.120.9:500",
        ),
    ),
)
def test_xqemu_network_forward_rule_get_rule_str(
    network_forward_rule: XQEMUNetworkForwardRule, expected_str: str,
):
    """Enusre that :py:class:`~pyxboxtest.xqemu.xqemu_params` gives the
    correct string
    """
    assert network_forward_rule.get_rule_str() == expected_str
