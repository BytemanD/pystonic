import asyncio

import httpx
from huey import crontab
from loguru import logger

from pystonic.huey.app import create_huery

HUEY = create_huery()

client = httpx.AsyncClient()


@HUEY.task(lock="test_url")
def test_url(url: str):
    logger.info("start test_url: {}", url)

    async def _run():
        for i in range(1, 11):
            resp = await client.get(url)
            logger.info("({}) GET {} -> {}", i, url, resp.status_code)
            resp = httpx.get(url)

        logger.info("test URL {} done", url)

    asyncio.run(_run())


@HUEY.periodic_task(crontab(minute="*/2"), lock="test_url")
def job_test_url():
    test_url("http://www.baidu.com")
