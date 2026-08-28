from enum import Enum
from ipaddress import AddressValueError, IPv4Address, IPv6Address
import re
from typing import List, Optional, Tuple

_TRUE_VALUES = ("true", "1", "on", "yes", "y", "ok", "enable")
_FALSE_VALUES = ("false", "0", "off", "no", "n", "nok", "disable")


def str2bool(value: str, strict=False) -> bool:
    if strict and value.lower() not in _TRUE_VALUES + _FALSE_VALUES:
        raise ValueError("Invalid value for boolean")
    return value.lower() in _TRUE_VALUES


class IPVersion(str, Enum):
    V4 = "v4"
    V6 = "v6"


def is_valid_ip(ip: str) -> Tuple[bool, Optional[IPVersion]]:
    try:
        IPv4Address(ip)
        return True, IPVersion.V4
    except AddressValueError:
        pass

    try:
        IPv6Address(ip)
        return True, IPVersion.V6
    except AddressValueError:
        pass
    return False, None


def find_code_blocks_from_markdown(markdown_text: str) -> List[str]:
    """Match command"""
    code_patterns = [
        r"```\w+\n(.*?)\n```",
        r"```\n(.*?)\n```",
        r"```(.*?)```",
    ]
    for pattern in code_patterns:
        code_blocks = re.findall(pattern, markdown_text, re.DOTALL)
        if code_blocks:
            return code_blocks
    return []


def text_shorten(text: str, wide: int = 100):
    if len(text) <= wide:
        return text
    return f"{text[:wide]} ..."
