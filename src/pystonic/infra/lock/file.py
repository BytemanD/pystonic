import contextlib
import os
import re
import tempfile

import portalocker
from loguru import logger

from pystonic.common.exceptions import GetLockTimeout


@contextlib.contextmanager
def get_lock(name: str, timeout: int = 2):
    # 清理锁名，防止路径穿越（如 name 含 "/" 或 ".."）
    safe_name = re.sub(r"[^\w.-]", "_", str(name)) or "lock"
    lock_path = os.path.join(tempfile.gettempdir(), f"{safe_name}.lock")
    logger.debug("get file lock: {} ...", name)
    try:
        with portalocker.Lock(lock_path, "w", timeout=timeout):
            logger.debug("get file lock: {} success", name)
            yield
    except portalocker.exceptions.AlreadyLocked:
        raise GetLockTimeout(name, timeout)
