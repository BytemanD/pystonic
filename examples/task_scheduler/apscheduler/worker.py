from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from pystonic.asgi.app import create_app
from pystonic.common.log import setup_logger
from pystonic.task_scheduler.drivers.apscheduler import APSchedulerDriver

from .tasks import sync_source

setup_logger(remove=True)

driver = APSchedulerDriver()


sources = {
    "1" * 32: "*/1 * * * *",
    "2" * 32: "*/2 * * * *",
    "3" * 32: "*/3 * * * *",
}

for source_id, crontab in sources.items():
    driver.add_crontab_job(
        crontab,
        sync_source,
        args=(source_id,),
        name=f"sync_source:{source_id}",
        id=f"sync_source:{source_id}",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    for job in driver.get_jobs():
        logger.info("job: {}", job)
    driver.start()
    yield
    driver.scheduler.shutdown()


API = create_app(lifespan=lifespan)
