from collections.abc import Callable
from datetime import timedelta

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from pystonic.common import context
from pystonic.common.conf import CONF
from pystonic.utils.dateutil import utcnow


class BaseManager:
    def __init__(self):
        self.host = CONF.hostname
        self.asyncio_scheduler = AsyncIOScheduler()
        self.backgroup_scheduler = BackgroundScheduler(
            executors={
                "default": ThreadPoolExecutor(
                    max_workers=CONF.scheduler.background_max_workers
                )
            }
        )
        self.shutdown = False

    def start(self):
        self.asyncio_scheduler.start()
        self.backgroup_scheduler.start()

    def stop(self):
        logger.info("shutdown scheduler")
        self.asyncio_scheduler.pause()
        self.backgroup_scheduler.pause()
        self.asyncio_scheduler.shutdown()
        self.backgroup_scheduler.shutdown()

    def get_context_account(self):
        return context.account()

    def get_backgroud_jobs(self):
        return self.backgroup_scheduler.get_jobs()

    def get_async_jobs(self):
        return self.asyncio_scheduler.get_jobs()

    def run_background_job(
        self,
        func: Callable,
        args: tuple | None = None,
        kwargs: dict | None = None,
        id: str | None = None,
        name: str | None = None,
        after_seconds: int = 0,
    ):
        """启动一次后台任务"""
        self.add_backgroud_job(
            DateTrigger(utcnow(delta=timedelta(seconds=after_seconds))),
            func,
            args=args,
            kwargs=kwargs,
            id=id,
            name=name,
        )

    def add_backgroud_job(
        self,
        trigger: BaseTrigger,
        func: Callable,
        args: tuple | None = None,
        kwargs: dict | None = None,
        id: str | None = None,
        name: str | None = None,
        max_instances: int = 1,
        coalesce=True,
    ):
        if max_instances <= 0:
            raise ValueError(
                f"max_instances must be a positive integer, got {max_instances}"
            )
        logger.info("add background job: {} with trigger: {}", func, trigger)
        self.backgroup_scheduler.add_job(
            func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            id=id,
            name=name,
            max_instances=max_instances,
            coalesce=coalesce,
        )

    def add_async_job(
        self,
        trigger: BaseTrigger,
        func: Callable,
        args: tuple | None = None,
        kwargs: dict | None = None,
        id: str | None = None,
        name: str | None = None,
        max_instances: int = 1,
        coalesce=True,
    ):
        if max_instances <= 0:
            raise ValueError(
                f"max_instances must be a positive integer, got {max_instances}"
            )

        logger.info("add background job: {} with trigger: {}", func, trigger)
        self.asyncio_scheduler.add_job(
            func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            id=id,
            name=name,
            max_instances=max_instances or 1,
            coalesce=coalesce,
        )
