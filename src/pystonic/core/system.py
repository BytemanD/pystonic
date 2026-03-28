import io
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from loguru import logger


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


def hostname():
    return socket.gethostname()


def ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(hostname())


def execute(
    cmd,
    check=True,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
):
    logger.debug("RUN: {}", cmd)
    process = subprocess.run(
        cmd, check=check, shell=shell, stdout=stdout, stderr=stderr
    )
    return process.returncode, process.stdout, process.stderr
