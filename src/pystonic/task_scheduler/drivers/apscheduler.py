import uuid
from datetime import datetime
from typing import Callable

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    JobEvent,
)
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger, timedelta
from loguru import logger

from pystonic.common.conf import CONF
from pystonic.common.exceptions import GetDBLockTimeout
from pystonic.orm import database


class DistributedThreadPoolExecutor(ThreadPoolExecutor):
    def submit_job(self, job: Job, run_times):
        try:
            with database.db_lock(job.id):
                return super().submit_job(job, run_times)
        except GetDBLockTimeout:
            event = JobEvent(EVENT_JOB_MISSED, job.id, job._jobstore_alias)
            self._scheduler._dispatch_event(event)
            return None


class APSchedulerDriver:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            executors={
                "default": DistributedThreadPoolExecutor(
                    max_workers=CONF.task_worker.max_workers
                )
            },
            # jobstores={"default": SQLAlchemyJobStore(url=CONF.db.url)},
        )
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)

    def _job_error_listener(self, event: JobEvent):
        if isinstance(event.exception, GetDBLockTimeout):
            return
        raise event.exception

    def start(self, paused: bool = False):
        logger.info("start scheduler")
        self.scheduler.start(paused=paused)

    def shutdown(self):
        logger.info("stop scheduler")
        self.scheduler.shutdown()

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def add_interval_job(
        self,
        job: Callable,
        args: set | None = None,
        kwargs: dict | None = None,
        id: str | None = None,
        name: str | None = None,
        **trigger_args,
    ):
        self.scheduler.add_job(
            job, "interval", args=args, kwargs=kwargs, id=id, name=name, **trigger_args
        )

    def add_crontab_job(
        self,
        crontab: str,
        job: Callable,
        args: set | None = (),
        kwargs: dict | None = {},
        id: str | None = None,
        name: str | None = None,
        max_instances: int = 1,
        coalesce: bool = True,
        replace_existing: bool = True,
        **trigger_args,
    ):
        self.scheduler.add_job(
            job,
            CronTrigger.from_crontab(crontab),
            args=args,
            kwargs=kwargs,
            id=id,
            name=name,
            max_instances=max_instances,
            coalesce=coalesce,
            replace_existing=replace_existing,
            **trigger_args,
        )

    def run_job(
        self,
        job: Callable,
        args: set | None = None,
        kwargs: dict | None = None,
        id: str | None = None,
        name: str | None = None,
    ):
        self.scheduler.add_job(
            job,
            "date",
            args=args,
            kwargs=kwargs,
            id=id or uuid.uuid4().hex,
            name=name,
            run_date=datetime.now() + timedelta(seconds=5),
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

    def remove_job(self, job_id: str):
        self.scheduler.remove_job(job_id)
