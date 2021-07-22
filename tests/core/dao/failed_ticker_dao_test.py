from datetime import datetime

import pytest


@pytest.fixture
def dao():
    from skogkatt.core.dao import dao_factory
    return dao_factory.get('FailedTickerDAO')


def test_insert(dao):
    data = {"date": datetime.now(), "job_name": "dao_test", "stock_code": "000020", "cause": "FileNotFound"}
    inserted = dao.insert(data)
    assert (1, inserted)


def test_update(dao):
    data = [{"date": datetime.now(), "job_name": "dao_test", "stock_code": "000020", "cause": "FileNotFound"}]
    try:
        temp = 1 / 0
    except ZeroDivisionError as err:
        data.append({"date": datetime.now(), "job_name": "dao_test", "stock_code": "000020", "cause": str(err)})

    updated = dao.update(data)
    assert (2, updated)


def test_find(dao):
    result = dao.find()
    assert (2, len(result))


def test_delete(dao):
    result = dao.delete(job_name="dao_test", stock_code="000020")
    assert(2, result)

