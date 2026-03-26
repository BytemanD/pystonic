from freezegun import freeze_time

from pystonic.utils import dateutil


def test_thisday():
    with freeze_time("2026-03-25 12:30:00"):
        start, end = dateutil.thisday()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-03-25 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-03-25 23:59:59"


def test_yestoday():
    with freeze_time("2026-03-25 12:30:00"):
        start, end = dateutil.yestoday()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-03-24 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-03-24 23:59:59"


def test_tormorrow():
    with freeze_time("2026-03-25 12:30:00"):
        start, end = dateutil.tormorrow()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-03-26 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-03-26 23:59:59"


def test_thisweek():
    with freeze_time("2026-03-19 12:30:00"):
        start, end = dateutil.thisweek()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-03-16 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-03-22 23:59:59"


def test_lastweek():
    with freeze_time("2026-03-19 12:30:00"):
        start, end = dateutil.lastweek()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-03-09 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-03-15 23:59:59"


def test_thismonth():
    with freeze_time("2026-03-19 12:30:00"):
        start, end = dateutil.thismonth()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-03-01 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-03-31 23:59:59"


def test_lastmonth():
    with freeze_time("2026-03-19 12:30:00"):
        start, end = dateutil.lastmonth()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-02-01 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-02-28 23:59:59"


def test_nextmonth():
    with freeze_time("2026-03-19 12:30:00"):
        start, end = dateutil.nextmonth()
        assert start.strftime(dateutil.FORMAT_DATETIME) == "2026-04-01 00:00:00"
        assert end.strftime(dateutil.FORMAT_DATETIME) == "2026-04-30 23:59:59"
