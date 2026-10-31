from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.date import DateTrigger

from pystonic.common.conf import CONF
from pystonic.manager import BaseManager


@pytest.fixture
def scheduler_mocks():
    """替换真实调度器，避免测试启动线程/事件循环"""
    with (
        patch("pystonic.manager.AsyncIOScheduler") as async_cls,
        patch("pystonic.manager.BackgroundScheduler") as background_cls,
        patch("pystonic.manager.ThreadPoolExecutor") as executor_cls,
    ):
        yield async_cls, background_cls, executor_cls


@pytest.fixture
def manager(scheduler_mocks):
    return BaseManager()


def test_init_uses_conf(manager, scheduler_mocks):
    async_cls, background_cls, executor_cls = scheduler_mocks

    assert manager.host == CONF.hostname
    assert manager.asyncio_scheduler is async_cls.return_value
    assert manager.backgroup_scheduler is background_cls.return_value
    assert manager.shutdown is False

    async_cls.assert_called_once_with()
    executor_cls.assert_called_once_with(
        max_workers=CONF.scheduler.background_max_workers
    )
    background_cls.assert_called_once_with(
        executors={"default": executor_cls.return_value}
    )


def test_start_starts_both_schedulers(manager, scheduler_mocks):
    async_cls, background_cls, _ = scheduler_mocks

    manager.start()

    async_cls.return_value.start.assert_called_once_with()
    background_cls.return_value.start.assert_called_once_with()


def test_stop_pauses_and_shuts_down_both_schedulers(manager, scheduler_mocks):
    async_cls, background_cls, _ = scheduler_mocks

    manager.stop()

    async_cls.return_value.pause.assert_called_once_with()
    async_cls.return_value.shutdown.assert_called_once_with()
    background_cls.return_value.pause.assert_called_once_with()
    background_cls.return_value.shutdown.assert_called_once_with()


def test_get_context_account(manager):
    with patch("pystonic.manager.context.account", return_value="alice") as account:
        assert manager.get_context_account() == "alice"

    account.assert_called_once_with()


def test_get_jobs(manager, scheduler_mocks):
    async_cls, background_cls, _ = scheduler_mocks
    async_cls.return_value.get_jobs.return_value = ["async-job"]
    background_cls.return_value.get_jobs.return_value = ["background-job"]

    assert manager.get_async_jobs() == ["async-job"]
    assert manager.get_backgroud_jobs() == ["background-job"]


def test_add_background_job(manager, scheduler_mocks):
    _, background_cls, _ = scheduler_mocks
    trigger = DateTrigger(run_date=datetime.now(UTC))
    func = MagicMock()

    manager.add_backgroud_job(
        trigger,
        func,
        args=(1, 2),
        kwargs={"foo": "bar"},
        id="job-1",
        name="demo",
        max_instances=2,
        coalesce=False,
    )

    background_cls.return_value.add_job.assert_called_once_with(
        func,
        trigger=trigger,
        args=(1, 2),
        kwargs={"foo": "bar"},
        id="job-1",
        name="demo",
        max_instances=2,
        coalesce=False,
    )


def test_add_async_job(manager, scheduler_mocks):
    async_cls, _, _ = scheduler_mocks
    trigger = DateTrigger(run_date=datetime.now(UTC))
    func = MagicMock()

    manager.add_async_job(
        trigger,
        func,
        args=(1, 2),
        kwargs={"foo": "bar"},
        id="job-1",
        name="demo",
        max_instances=2,
        coalesce=False,
    )

    async_cls.return_value.add_job.assert_called_once_with(
        func,
        trigger=trigger,
        args=(1, 2),
        kwargs={"foo": "bar"},
        id="job-1",
        name="demo",
        max_instances=2,
        coalesce=False,
    )


@pytest.mark.parametrize("max_instances", [0, -1])
def test_add_background_job_rejects_invalid_max_instances(
    manager, scheduler_mocks, max_instances
):
    _, background_cls, _ = scheduler_mocks

    with pytest.raises(ValueError, match="max_instances must be a positive integer"):
        manager.add_backgroud_job(
            MagicMock(spec=BaseTrigger),
            MagicMock(),
            max_instances=max_instances,
        )

    background_cls.return_value.add_job.assert_not_called()


@pytest.mark.parametrize("max_instances", [0, -1])
def test_add_async_job_rejects_invalid_max_instances(
    manager, scheduler_mocks, max_instances
):
    async_cls, _, _ = scheduler_mocks

    with pytest.raises(ValueError, match="max_instances must be a positive integer"):
        manager.add_async_job(
            MagicMock(spec=BaseTrigger),
            MagicMock(),
            max_instances=max_instances,
        )

    async_cls.return_value.add_job.assert_not_called()


@pytest.mark.parametrize("after_seconds", [0, 5])
def test_run_background_job(manager, after_seconds):
    func = MagicMock()
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    def fake_utcnow(delta=None):
        return now + (delta or timedelta())

    with (
        patch.object(manager, "add_backgroud_job") as add_job,
        patch("pystonic.manager.utcnow", side_effect=fake_utcnow) as utcnow,
    ):
        manager.run_background_job(
            func,
            args=(1,),
            kwargs={"foo": "bar"},
            id="job-1",
            name="demo",
            after_seconds=after_seconds,
        )

    utcnow.assert_called_once_with(delta=timedelta(seconds=after_seconds))
    trigger = add_job.call_args.args[0]
    assert isinstance(trigger, DateTrigger)
    assert trigger.run_date == now + timedelta(seconds=after_seconds)
    add_job.assert_called_once_with(
        trigger,
        func,
        args=(1,),
        kwargs={"foo": "bar"},
        id="job-1",
        name="demo",
    )
