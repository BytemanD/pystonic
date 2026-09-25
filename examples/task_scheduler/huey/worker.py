from threading import Thread

import uvicorn
from fastapi import FastAPI
from huey import crontab
from jaraco import functools

from pystonic.common import context
from pystonic.common.log import setup_logger

from .tasks import HUEY, sync_source

setup_logger(remove=True)


@HUEY.pre_execute()
def set_context(task):
    context.set_trace()


sources = {
    "1" * 32: crontab(minute="*/1"),
    "2" * 32: crontab(minute="*/2"),
    "3" * 32: crontab(minute="*/3"),
}

for source_id, validate_time in sources.items():
    HUEY.periodic_task(
        validate_time,
        name=f"sync_source:{source_id}",
        lock=f"job_sync_source:{source_id}",
    )(functools.partial(sync_source, source_id))


# API for health check
API = FastAPI()


@API.get("/livez")
async def livez():
    return {}


api_thread = Thread(target=uvicorn.run, args=(API,), kwargs={"port": 8001}, daemon=True)
api_thread.start()
