import contextlib

from loguru import logger
from redis.exceptions import LockError

from pystonic.common.exceptions import GetLockTimeout
from pystonic.infra.redis.client import RedisClient

r = RedisClient()

# 锁的自动过期时间(TTL)，防止持锁进程崩溃后死锁
LOCK_TTL = 60


@contextlib.contextmanager
def get_lock(name: str, timeout: int = 2):
    """Redis 分布式锁

    Args:
        name: 锁名
        timeout: 获取锁的等待超时秒数（非锁过期时间）
    """
    lock = r.client.lock(name, timeout=LOCK_TTL, blocking_timeout=timeout)
    logger.debug("get redis lock: {} ...", name)
    if not lock.acquire(blocking=True):
        logger.debug("get redis lock: {} timeout", name)
        raise GetLockTimeout(name, timeout)
    logger.debug("get redis lock: {} success", name)
    try:
        yield
    finally:
        try:
            lock.release()
        except LockError as e:
            # 临界区超过 TTL，锁已自动释放
            logger.warning("release redis lock: {} failed: {}", name, e)
