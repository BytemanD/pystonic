import contextlib

from redis.exceptions import LockError
from pystonic.common.exceptions import GetLockTimeout
from pystonic.infra.redis.client import RedisClient

r = RedisClient()


@contextlib.contextmanager
def get_lock(name: str, timeout: int = 2):
    try:
        with r.lock(name, timeout=timeout):
            # 成功获取锁，执行临界区代码
            yield
    except LockError:
        raise GetLockTimeout(name, timeout)
