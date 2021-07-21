import re
from datetime import datetime
from typing import Any, Tuple

from dateutil.relativedelta import relativedelta


def days_between(d1, d2):
    """
    Returns the number of days between the start and end dates
    :param d1: start date
    :param d2: end date
    :return: the number of days
    """
    if type(d1) != type(d2):
        raise TypeError(f"Cannot calculate in different types '{type(d1)}' and {type(d2)}")

    if isinstance(d1, str):
        d1 = re.sub("\\D", "", d1)
        d2 = re.sub("\\D", "", d2)
        d1 = datetime.strptime(d1, '%Y%m%d')
        d2 = datetime.strptime(d2, '%Y%m%d')

    d1 = d1.replace(hour=0, minute=0, second=0, microsecond=0)
    d2 = d2.replace(hour=0, minute=0, second=0, microsecond=0)

    return (d2 - d1).days


def years_between(d1, d2):
    """
    Returns the number of years between the start and end dates
    :param d1: start date
    :param d2: end date
    :return: the number of years
    """
    return int(days_between(d1, d2) / 365)


def get_fiscal_date(date: Any = None) -> (int, int):
    t_date = date if date is not None else datetime.today()

    if isinstance(date, str):
        date = re.sub("\\D", "", date)
        t_date = datetime.strptime(date, '%Y%m%d')

    # fiscal_date = t_date - relativedelta(years=1)
    fiscal_date = t_date - relativedelta(months=3)
    fiscal_quarter = get_quarter(fiscal_date.month)

    fiscal_month = 3 * fiscal_quarter
    fiscal_year = fiscal_date.year

    return fiscal_year, fiscal_month


def get_prev_quarters(count, year=None, month=None):
    dates = []
    today = datetime.today()
    year = year if year is not None else today.year
    month = month if month is not None else today.month

    start = datetime(year=year, month=month, day=1)
    # start = start - relativedelta(months=3)

    for i in range(count):
        prev_date = start - relativedelta(months=3)
        dates.insert(0, (prev_date.year, 3 * get_quarter(prev_date.month)))
        start = prev_date

    return dates


def get_quarter(month: int):
    return (month - 1) // 3 + 1


def get_quarter_periods(count_quarters: int = 5) -> Tuple:
    """
    분기자료 검색시 사용할 시작, 종료일 반환.
    오늘 날짜를 기준으로 직전분기까지 count_quarters 수 만큼 년/월을 계산해서
    시작, 끝 분기 년/월을 반환한다.
    :param count_quarters: 분기수, default 5분기
    :return:
    """
    dates = get_prev_quarters(count_quarters)

    date_from = f'{dates[0][0]}/{dates[0][1]:02d}'
    date_to = f'{dates[-1][0]}/{dates[-1][1]:02d}'
    return date_from, date_to


def get_annual_periods(count_years: int = 5) -> Tuple:
    """
    연간자료 검색시 사용할 시작, 종료일 반환.
    오늘 날짜를 기준으로 직전년도까지 count_years 수 만큼 년/월을 계산해서
    시작, 끝 년/월을 반환한다.
    :param count_years: 년수
    :return:
    """
    current = datetime.today()
    from_year = current.year - count_years
    to_year = current.year - 1
    return f'{from_year}/12', f'{to_year}/12'
