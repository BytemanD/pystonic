import asyncio
import time

import httpx
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
