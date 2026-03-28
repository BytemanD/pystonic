import pytest
from pystonic.core.strutil import str2bool, is_valid_ip, IPVersion


def test_str2bool_true_values():
    """测试真值字符串"""
    true_values = ["true", "True", "TRUE", "1", "on", "On", "yes", "y", "ok", "enable"]
    for value in true_values:
        assert str2bool(value) is True


def test_str2bool_false_values():
    """测试假值字符串"""
    false_values = [
        "false",
        "False",
        "FALSE",
        "0",
        "off",
        "Off",
        "no",
        "n",
        "nok",
        "disable",
    ]
    for value in false_values:
        assert str2bool(value) is False


def test_str2bool_strict_mode_valid():
    """测试严格模式下的有效值"""
    assert str2bool("true", strict=True) is True
    assert str2bool("false", strict=True) is False


def test_str2bool_strict_mode_invalid():
    """测试严格模式下的无效值抛出异常"""
    with pytest.raises(ValueError, match="Invalid value for boolean"):
        str2bool("invalid", strict=True)


def test_str2bool_non_strict_mode_default():
    """测试非严格模式下未知值返回 False"""
    assert str2bool("unknown") is False
    assert str2bool("maybe") is False


def test_is_valid_ip_ipv4():
    """测试有效的 IPv4 地址"""
    ipv4_addresses = [
        "192.168.1.1",
        "10.0.0.1",
        "255.255.255.255",
        "0.0.0.0",
        "127.0.0.1",
    ]
    for ip in ipv4_addresses:
        is_valid, version = is_valid_ip(ip)
        assert is_valid is True
        assert version == IPVersion.V4


def test_is_valid_ip_ipv6():
    """测试有效的 IPv6 地址"""
    ipv6_addresses = [
        "::1",
        "fe80::1",
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "2001:db8::1",
        "::",
    ]
    for ip in ipv6_addresses:
        is_valid, version = is_valid_ip(ip)
        assert is_valid is True
        assert version == IPVersion.V6


def test_is_valid_ip_invalid():
    """测试无效的 IP 地址"""
    invalid_addresses = [
        "256.256.256.256",
        "192.168.1",
        "192.168.1.1.1",
        "invalid",
        "",
        "192.168.1.-1",
        "gggg::1",
    ]
    for ip in invalid_addresses:
        is_valid, version = is_valid_ip(ip)
        assert is_valid is False
        assert version is None


def test_is_valid_ip_returns_tuple():
    """测试返回值格式为元组"""
    result = is_valid_ip("192.168.1.1")
    assert isinstance(result, tuple)
    assert len(result) == 2

    is_valid, version = result
    assert is_valid is True
    assert isinstance(version, IPVersion)
