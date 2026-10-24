import contextlib
import os
import tempfile

import portalocker
from loguru import logger

from pystonic.common.exceptions import GetLockTimeout


@contextlib.contextmanager
def get_lock(name: str, timeout: int = 2):
    lock_path = os.path.join(tempfile.gettempdir(), f"{name}.lock")
    logger.debug("get file lock: {} ...", name)
    try:
        with portalocker.Lock(lock_path, "w", timeout=timeout):
            logger.debug("get file lock: {} success", name)
            yield
    except portalocker.exceptions.AlreadyLocked:
        raise GetLockTimeout(name, timeout)
