import io
import os
import platform
import shutil
import sys
from pathlib import Path


def is_windows():
    return platform.system() == "Window"


def is_linux():
    return platform.system() == "Linux"


def reset_encoding(encoding="utf-8"):
    if sys.stdout.encoding != encoding:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=encoding)
    if sys.stderr.encoding != encoding:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=encoding)


def home_path():
    return Path(os.path.expanduser("~"))


def dot_config():
    return home_path().joinpath(".config")


def cpu_count():
    return os.cpu_count()

def disk_usage(path: Path):
    return shutil.disk_usage(path)
