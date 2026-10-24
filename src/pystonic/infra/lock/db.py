import contextlib

from loguru import logger
from sqlmodel import text

from pystonic.common.exceptions import GetDBLockTimeout
from pystonic.orm.database import get_session


@contextlib.contextmanager
def get_lock(name, timeout: int = 2):
    with get_session() as session:
        logger.debug("get db lock: {}", name)
        result = session.exec(text(f"SELECT GET_LOCK('{name}', {timeout});")).first()
        if not result or result[0] != 1:
            logger.debug("get lock: {} timeout", name)
            raise GetDBLockTimeout(name, timeout)
        logger.debug("get file lock: {} success", name)
        yield
