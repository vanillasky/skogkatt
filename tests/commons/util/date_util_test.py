import pytest

from skogkatt.commons.util.date import get_fiscal_date, get_prev_quarters


@pytest.mark.util
def test_get_fiscal_date():
    str_dates = ['2021-06-16', '2021-01-03', '2021-08-18']
    expected = [(2021, 3), (2020, 12), (2021, 6)]
    for i in range(len(str_dates)):
        (year, month) = get_fiscal_date(str_dates[i])
        assert (expected[i] == (year, month))


@pytest.mark.util
def test_get_prev_quarters():
    quarters = get_prev_quarters(4, 2021, 6)
    expected = [(2020, 6), (2020, 9), (2020, 12), (2021, 3)]
    assert (expected == quarters)

    quarters = get_prev_quarters(4, 2021, 1)
    expected = [(2020, 3), (2020, 6), (2020, 9), (2020, 12)]
    assert (expected == quarters)
