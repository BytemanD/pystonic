import asyncio

import httpx
from loguru import logger

from pystonic.common import context

client = httpx.AsyncClient()


@context.with_trace_id
def sync_source(source_id: str):

    async def _run():
        for i in range(1, 11):
            await asyncio.sleep(1)

    logger.info("start sync source: {}", source_id)
    asyncio.run(_run())
    logger.success("sync source {} done", source_id)
