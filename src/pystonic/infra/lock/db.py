import contextlib

from loguru import logger
from sqlmodel import text

from pystonic.common.exceptions import GetDBLockTimeout
from pystonic.orm.database import get_session


@contextlib.contextmanager
def get_lock(name, timeout: int = 2):
    """基于 MySQL 命名锁的分布式锁

    Args:
        name: 锁名（绑定在当前会话连接上, 仅支持 MySQL）
        timeout: GET_LOCK 等待超时秒数
    """
    with get_session() as session:
        logger.debug("get db lock: {}", name)
        result = session.exec(
            text("SELECT GET_LOCK(:name, :timeout)"), {"name": name, "timeout": timeout}
        ).first()
        if not result or result[0] != 1:
            logger.debug("get lock: {} timeout", name)
            raise GetDBLockTimeout(name, timeout)
        try:
            yield
        finally:
            # 命名锁绑定连接，显式释放后再归还连接池，避免锁随池化连接泄漏
            session.exec(text("SELECT RELEASE_LOCK(:name)"), {"name": name})
            logger.debug("release lock: {} success", name)
