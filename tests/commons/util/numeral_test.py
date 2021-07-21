import pytest

from skogkatt.commons.util.numeral import format_with, to_decimal


@pytest.mark.parametrize("num, output", [
    ("000100000000", "100,000,000"),
    ("100000000", "100,000,000"),
    ("-12345678", "-12,345,678"),
    ("-12345.08", "-12,345.08"),
    ("1234567", "1,234,567")
])
def test_format_with(num, output):
    assert format_with(num) == output


@pytest.mark.parametrize("str_num, output", [
    ("000100000000", 100000000),
    ("100000000", 100000000),
    ("-12345678", -12345678),
    ("-12345.08", -12345.08),
    ("1234567", 1234567)
])
def test_to_decimal(str_num, output):
    assert to_decimal(str_num) == output

