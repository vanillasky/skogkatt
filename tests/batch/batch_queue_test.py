import pytest
from skogkatt.conf.app_conf import app_config, Config


@pytest.fixture
def setup(request):
    app_config.set_mode(Config.TEST)

    from skogkatt.batch.queue_factory import queue_factory
    from skogkatt.core.ticker.store import ticker_store

    def teardown():
        app_config.restore()
        queue_factory.remove_batch_queue(__name__)
        queue_factory.remove_batch_queue("queue_for_batch2")

    request.addfinalizer(teardown)

    return queue_factory, ticker_store


def test_create_queue(setup):
    queue_factory, ticker_store = setup
    """ 주식 종목코드 개수만큼 큐에 등록 되었는지 확인 """
    tickers = ticker_store.get_tickers()
    queue1 = queue_factory.create(__name__)
    assert (len(tickers) == queue1.qsize())

    queue2 = queue_factory.create("queue_for_batch2")
    assert (len(tickers) == queue2.qsize())

    queue1_searched = queue_factory.get_queue(__name__)
    queue2_searched = queue_factory.get_queue("queue_for_batch2")
    assert (len(tickers) == queue1_searched.qsize())
    assert (len(tickers) == queue2_searched.qsize())


def test_delete_queue(setup):
    queue_factory, ticker_store = setup
    """ 큐 자료 삭제 """
    tickers = ticker_store.get_tickers()
    queue = queue_factory.create(__name__)
    assert (len(tickers) == queue.qsize())

    queue_factory.remove_queue_item(__name__, stock_code="005930")
    queue = queue_factory.get_queue(__name__)
    assert (len(tickers) - 1 == queue.qsize())


def test_assign_queue(setup):
    queue_factory, ticker_store = setup

    stock_codes = ['005930', '051910']
    queue_factory.assign_queue(__name__, stock_codes)
    queue = queue_factory.get_queue(__name__)
    assert (len(stock_codes) == queue.qsize())
