import time
from datetime import datetime

import pytest

from skogkatt.batch import BatchStatus
from skogkatt.conf.app_conf import app_config, Config


@pytest.fixture
def status_dao(request):
    app_config.set_mode(Config.TEST)

    from skogkatt.core.dao import dao_factory
    from skogkatt.core.dao.idao import BatchStatusDAO
    from skogkatt.batch import BatchStatus

    dao: BatchStatusDAO = dao_factory.get('BatchStatusDAO')
    test_status = BatchStatus('StatusDAO Test', datetime.now())
    if dao.get_engine().exists_table(dao.get_table_name()):
        dao.update(test_status)

    def teardown():
        dao.delete()

    request.addfinalizer(teardown)

    return dao, test_status


def test_find(status_dao):
    status_dao, test_status = status_dao
    count = status_dao.count()
    status_list = status_dao.find()
    assert (count == len(status_list))

    df = status_dao.find(as_dataframe=True)
    assert (count == df.shape[0])

    filtered_df = status_dao.find(batch_name=test_status.name, as_dataframe=True)
    # print(tabulate(filtered_df, headers="keys", tablefmt="psql"))
    assert (filtered_df.shape[0] > 0)

    recent = status_dao.find(batch_name=test_status.name, limit=1)
    assert (1 == len(recent))


def test_insert(status_dao):
    status_dao, test_status = status_dao
    status = BatchStatus('insert 테스트', datetime.now())
    status_dao.insert(status)

    status_list = status_dao.find(batch_name=status.name, limit=1)
    assert ('insert 테스트' == status_list[0].name)


def test_update(status_dao):
    status_dao, test_status = status_dao

    """ INSERT MODE """
    status = BatchStatus('update 테스트', datetime.now())
    status_dao.update(status)

    status_list = status_dao.find(batch_name=status.name, limit=1)
    assert ('update 테스트' == status_list[0].name)

    """ UPDATE MODE """
    time.sleep(3)
    status.status = 0
    status.end = datetime.now()
    status.elapsed = status.end - status.start
    status_dao.update(status)

    prev_start = status.start.strftime("%y-%m-%d %H:%M:%S")
    status_list = status_dao.find(batch_name=status.name)
    assert (1 == len(status_list))
    assert (status.name == status_list[0].name)
    start = status_list[0].start.strftime("%y-%m-%d %H:%M:%S")
    assert (prev_start, start)
    assert (status.end is not None)
