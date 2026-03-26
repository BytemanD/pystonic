import calendar
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

FORMAT_DATE = "%Y-%m-%d"
FORMAT_TIME = "%H:%M:%S"
FORMAT_DATETIME = f"{FORMAT_DATE} {FORMAT_TIME}"


def day_range(days_offset=0, date: datetime = None):
    """
    获取指定日期的起止时间范围

    Args:
        date: 指定日期, None表示今天
        days_offset: 偏移天数, 0=今天，-1=昨天, 1=明天

    Returns:
        tuple: (开始时间, 结束时间)
    """
    if date is None:
        date = datetime.now()

    target_date = date + timedelta(days=days_offset)
    start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start, end


def thisday():
    return day_range(days_offset=0)


def yestoday():
    return day_range(days_offset=-1)


def tormorrow():
    return day_range(days_offset=1)


def week_range(week_offset: int = 0, date: datetime = None):
    """获取指定周的起止时间范围"""
    if date is None:
        date = datetime.now()
    monday = date - timedelta(days=date.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0), sunday.replace(
        hour=23, minute=59, second=59, microsecond=999999
    )


def thisweek():
    return week_range()


def lastweek():
    return week_range(-1)


def month_range(month_offset: int = 0, date: datetime = None):
    """获取指定周的起止时间范围"""
    if date is None:
        date = datetime.now()
    if month_offset != 0:
        date = date + relativedelta(months=month_offset)

    first_day = datetime(date.year, date.month, 1, 0, 0, 0)
    last_day = first_day + relativedelta(
        days=calendar.monthrange(date.year, date.month)[1] - 1,
        hours=23,
        minutes=59,
        seconds=59,
        microseconds=999999,
    )
    return first_day, last_day


def thismonth():
    return month_range()


def lastmonth():
    return month_range(-1)


def nextmonth():
    return month_range(1)
