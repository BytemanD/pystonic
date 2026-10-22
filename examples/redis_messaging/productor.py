import time
import uuid

from examples.redis_messaging.objects import Knowledge
from pystonic.common.log import setup_logger
from pystonic.infra.redis.messaging import Productor

setup_logger(remove=True)


productor = Productor()
while True:
    productor.push("foo:knowledges", Knowledge(uuid=uuid.uuid4().hex, path="/file/path"))
    time.sleep(0.5)
