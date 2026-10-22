from examples.redis_messaging.objects import Knowledge
from pystonic.common.log import setup_logger
from pystonic.infra.redis.messaging import Consumer

setup_logger(remove=True)
consumer = Consumer()
for item in consumer.watch("foo:knowledges", response_model=Knowledge):
    print('receive item ->', item)
