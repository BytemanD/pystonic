import threading

from loguru import logger
from pydantic import BaseModel, ValidationError

from pystonic.infra.redis.client import RedisClient
from pystonic.utils.system import getpid, hostname


class RedisMessaingQueue:
    def __init__(self, group_name: str | None = None, consumer_name: str | None = None):
        self.group_name = group_name or f"Host-{hostname()}"
        self.consumer_name = consumer_name or f"Thread-{getpid()}"
        self.redis = RedisClient(decode_responses=True)
        self._shutdown_event = threading.Event()

    def shutdown(self):
        self.redis.client.close()
        self._shutdown_event.set()

    def publish(self, name: str, value: BaseModel):
        self.redis.xadd(name, value.model_dump(mode="json"))

    def consume(
        self,
        name: str,
        count: int = 1,
        block: int = 5000,
        response_model: type[BaseModel] | None = None,
    ):
        self.redis.x_create_group(name, self.group_name, mkstream=True)
        logger.info("watch redis key: {}", name)
        while not self._shutdown_event.is_set():
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
                    try:
                        item = (
                            response_model.model_validate(fields)
                            if response_model
                            else fields
                        )
                    except ValidationError:
                        logger.error("invalid {}: {}", response_model, fields)
                        continue
                    yield item
                    logger.debug("ack {}", msg_id)
                    self.redis.client.xack(name, self.group_name, msg_id)
