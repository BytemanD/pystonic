import subprocess
from typing import Optional

from loguru import logger


def execute(cmd: str, check=True, success_code: Optional[int] = 0):
    """执行系统命令"""
    logger.debug("RUN: {}", cmd)
    status, output = subprocess.getstatusoutput(cmd)
    if check and status != 0:
        raise subprocess.CalledProcessError(status, cmd=cmd, stderr=output)
    return status, output
