from os import getpid
from typing import Type

from loguru import logger
from pydantic import BaseModel

from pystonic.infra.redis.client import RedisClient
from pystonic.utils.system import hostname


class Productor:
    def __init__(self):
        self.redis = RedisClient(decode_responses=True)

    def push(self, name: str, value: BaseModel):
        self.redis.xadd(name, value.model_dump(mode="json"))


class Consumer:
    def __init__(self, group_name: str | None = None, consumer_name: str | None = None):
        self.group_name = group_name or f"Host-{hostname()}"
        self.consumer_name = consumer_name or f"Thread-{getpid()}"
        self.redis = RedisClient(decode_responses=True)

    def watch(
        self,
        name: str,
        count: int = 1,
        block: int = 5000,
        response_model: Type[BaseModel] | None = None,
    ):
        self.redis.x_create_group(name, self.group_name, mkstream=True)
        logger.info("watch redis key: {}", name)
        while True:
            results = self.redis.x_read_group(
                name,
                self.group_name,
                self.consumer_name,
                count=count,
                block=block,
            )

            if not results:
                continue
            logger.debug("receive {} results", len(results))
            for stream_name, messages in results:
                for msg_id, fields in messages:
                    yield (
                        response_model.model_validate(fields)
                        if response_model
                        else fields
                    )
                    logger.debug("ack {}", msg_id)
                    self.redis.client.xack(name, self.group_name, msg_id)
