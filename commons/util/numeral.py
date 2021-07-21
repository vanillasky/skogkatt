from typing import Any


def to_decimal(value: str) -> int or float:
    """
    int 또는 float 으로 형변환
    :param value: string value
    :return: int or float or None if cannot convert type
    """
    result = value.lstrip('0')
    if result == '' or result == '00':
        return 0

    try:
        result = int(value)
    except ValueError:
        try:
            result = float(value)
        except ValueError:
            return None

    return result


def format_with(value: Any, separator=',') -> str:
    decimal_value = to_decimal(value) if isinstance(value, str) else value

    try:
        formatted = format(decimal_value, f"-{separator}")
    except ValueError:
        return value

    return formatted


def value_of(obj: Any) -> str:
    return 'None' if obj is None else str(obj)


