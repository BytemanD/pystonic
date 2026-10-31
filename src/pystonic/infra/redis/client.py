import redis
from redis.exceptions import ResponseError, TimeoutError

from pystonic.common.conf import CONF


class RedisClient:
    """Redis client
    Usage:

    >>> client = RedisClient()
    >>> client.set("foo", "hello")
    >>> print(client.get("foo"))
    """

    def __init__(self, decode_responses=False):
        self.client = redis.Redis.from_url(
            CONF.redis.url, decode_responses=decode_responses
        )

    def set(self, name: str, value: str, ex: int | None = None):
        self.client.set(name, value, ex=ex)

    def get(self, name: str):
        value = self.client.get(name)
        if not value:
            return value
        if isinstance(value, bytes):
            return value.decode()
        return value

    def xadd(self, name: str, value: dict):
        self.client.xadd(name, value)

    def x_create_group(self, name: str, group_name: str, mkstream: bool = False):
        try:
            self.client.xgroup_create(name, group_name, mkstream=mkstream)
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def x_read_group(
        self,
        name: str,
        group_name: str,
        consumer_name: str,
        count=1,
        block=5000,
    ):
        try:
            return self.client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={name: ">"},
                count=count,
                block=block,
            )
        except TimeoutError:
            return None
