import dataclasses
from typing import Dict, List, Optional

import psutil
from pydantic import BaseModel


class DiskUsage(BaseModel):
    total: int
    used: int
    free: int
    percent: float


class Disk(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    opts: str = ""
    usage: Optional[DiskUsage] = None


class NetInterface(BaseModel):
    name: str
    mac_address: str = ""
    addresses: List[str] = dataclasses.field(default_factory=list)
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0


class CPUInfo(BaseModel):
    count: int | None
    count_logical: int | None
    percent: float


class MemoryInfo(BaseModel):
    total: int
    available: int
    used: int
    percent: float


def cpu_usage():
    return CPUInfo(
        count=psutil.cpu_count(logical=False),
        count_logical=psutil.cpu_count(),
        percent=psutil.cpu_percent(interval=1),
    )


def virtual_memory():
    mem = psutil.virtual_memory()
    return MemoryInfo(
        total=mem.total,
        available=mem.available,
        used=mem.used,
        percent=mem.percent,
    )


def disk_usage(mountpoint: str = "/"):
    disk = psutil.disk_usage(mountpoint)
    return DiskUsage(
        total=disk.total, used=disk.used, free=disk.free, percent=disk.percent
    )


def partitions(all_device=False) -> List[Disk]:
    """获取所有磁盘分区信息

    如果 all_device=False, 仅物理设备
    """
    partitions = psutil.disk_partitions(all=all_device)
    return [
        Disk(
            device=part.device,
            mountpoint=part.mountpoint,
            fstype=part.fstype,
            opts=part.opts,
            usage=disk_usage(part.mountpoint),
        )
        for part in partitions
        if part.device and part.fstype not in ["cgroup", "cgroup2", "tmpfs"]
    ]


def net_interfaces(self) -> List[NetInterface]:
    """获取网络接口地址信息"""
    net_ifs: Dict[str, NetInterface] = {}
    addrs = psutil.net_if_addrs()
    for interface, addresses in addrs.items():
        if interface == "lo":
            continue
        net_ifs[interface] = NetInterface(name=interface)
        for addr in addresses:
            if addr.family.name in ["AF_LINK", "AF_PACKET"]:
                net_ifs[interface].mac_address = addr.address
            else:
                net_ifs[interface].addresses.append(addr.address)

    net_io = psutil.net_io_counters(pernic=True)
    for interface, stats in net_io.items():
        if interface not in net_ifs:
            continue
        net_ifs[interface].bytes_sent = stats.bytes_sent
        net_ifs[interface].bytes_recv = stats.bytes_recv
        net_ifs[interface].packets_sent = stats.packets_sent
        net_ifs[interface].packets_recv = stats.packets_recv

    return list(net_ifs.values())
