import asyncio
import functools
import time

import httpx
from huey import crontab
from loguru import logger

from pystonic.task_scheduler.huey.app import create_huery

HUEY = create_huery()

client = httpx.AsyncClient()


@HUEY.task(lock="test_url")
def sync_source(source_id: str):

    async def _run():
        for i in range(1, 11):
            time.sleep(1)

    logger.info("start sync source: {}", source_id)
    asyncio.run(_run())
    logger.success("sync source {} done", source_id)


sources = {
    "1" * 32: crontab(minute="*/1"),
    "2" * 32: crontab(minute="*/2"),
    "3" * 32: crontab(minute="*/3"),
}

for source_id, validate_time in sources.items():
    # def job_sync_source():
    #     sync_source(source_id)

    HUEY.periodic_task(
        validate_time,
        name=f"sync_source:{source_id}",
        lock=f"job_sync_source:{source_id}",
    )(functools.partial(sync_source, source_id))
