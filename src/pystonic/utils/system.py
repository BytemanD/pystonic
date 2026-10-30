import io
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import distro
from loguru import logger
from pydantic import BaseModel

from pystonic import app_name


def is_windows():
    return platform.system() == "Windows"


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
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:  # noqa: BLE001
        return socket.gethostbyname(hostname())


def getpid():
    return os.getpid()


def get_all_non_loopback_ips():
    """使用 socket 获取所有非回环 IP"""
    return [ip for ip in socket.gethostbyname_ex(hostname())[2] if ip != "127.0.0.1"]


def get_first_non_loopback_ip(default: str | None = None):
    """使用 socket 获取所有非回环 IP"""
    ips = get_all_non_loopback_ips()
    if not ips and not default:
        raise ValueError("No non-loopback IP found")
    return ips[0] if ips else default


def execute(
    *args: str,
    shell=False,
    check=False,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
):
    logger.debug("Run: {}", args)
    process = subprocess.run(
        [x for x in args],
        shell=shell,
        text=text,
        check=check,
        stdout=stdout,
        stderr=stderr,
    )
    return process.returncode, process.stdout, process.stderr


def global_app_data(name: str | None = None) -> Path:
    """获取全局数据目录"""
    appdir = os.getenv("APPDATA")
    if not appdir:
        appdir = "/usr/share"
    return Path(appdir, name or app_name())


def user_app_data(name: str | None = None) -> Path:
    """获取用户级数据目录"""
    return home_path().joinpath(f".{name or app_name()}")


class PlatformInfo(BaseModel):
    system: str
    release: str
    version: str
    machine: str
    processor: str
    name: str | None = None
    dist_version: str | None = None


def platform_info():
    info = PlatformInfo(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        processor=platform.processor(),
    )
    if platform.system().lower() == "linux":
        info.name = distro.name()
        info.dist_version = distro.version()

    return info
