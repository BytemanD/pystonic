from examples.redis_messaging.objects import Knowledge
from pystonic.common.log import setup_logger
from pystonic.infra.messaging.redis import RedisMessaingQueue

setup_logger(remove=True)
mq = RedisMessaingQueue()
for item in mq.consume("foo:knowledges", response_model=Knowledge):
    print('receive item ->', item)
