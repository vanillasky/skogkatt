import pytest

from skogkatt.conf.app_conf import app_config, Config


class Mock:
    from skogkatt.core.decorators import batch_status
    """
    배치 데코레이터 테스트용
    """

    @batch_status(batch_name='decorator_test')
    def division_by_zero(self):
        val = 1 / 0

    @batch_status(batch_name='mock')
    def say_hello(self):
        print("crawler function")


@pytest.fixture
def monitor(request):
    app_config.set_mode(Config.TEST)

    from skogkatt.batch.monitor import BatchMonitor
    from skogkatt.core.dao import dao_factory
    from skogkatt.core.dao.idao import BatchStatusDAO

    monitor = BatchMonitor()
    dao: BatchStatusDAO = dao_factory.get("BatchStatusDAO")

    def teardown():
        app_config.restore()
        dao.delete("decorator_test")
        dao.delete("mock")

    request.addfinalizer(teardown)

    return monitor


def test_normal_method(monitor):
    """
    정상 종료, status.status = 0
    :return:
    """
    mock = Mock()
    mock.say_hello()
    status = monitor.get_status('mock')
    assert ('mock', status.name)
    assert (0, status.status)


def test_division_by_zero(monitor):
    """
    에러발생, status.status = -1
    :return:
    """
    mock = Mock()
    try:
        mock.division_by_zero()
    except ZeroDivisionError:
        assert True

    status = monitor.get_status('decorator_test')
    assert ('decorator_test', status.name)
    assert (-1, status.status)
