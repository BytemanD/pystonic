import io
import platform
import sys


def is_windows():
    return platform.system() == "Window"


def is_linux():
    return platform.system() == "Linux"


def reset_encoding(encoding="utf-8"):
    if sys.stdout.encoding != encoding:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=encoding)
    if sys.stderr.encoding != encoding:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=encoding)
