import sys
from datetime import datetime, timedelta

import pytest
from PyQt5.QtWidgets import QApplication
from tabulate import tabulate

from skogkatt.conf.app_conf import app_config, Config


""" 메소드별로 테스트 필요. 일괄 실행시 QEventLoop 때문에 에러발생하는 것으로 보임. 미해결 상태 """


app_config.set_mode(Config.TEST)

STOCK_CODE = '005930'
account_no = app_config.get("MOCK_ACCOUNT_NO")


@pytest.fixture
def q_app():
    app = QApplication(sys.argv)

    yield app


@pytest.fixture
def dao():
    from skogkatt.core.dao import dao_factory
    return dao_factory.get('DailyChartDAO')


@pytest.fixture
def setup(q_app, request):
    from skogkatt.core.ticker.store import ticker_store
    from skogkatt.api.kiwoom.broker import KiwoomBroker
    from skogkatt.api.kiwoom.collector import ChartCollector

    ticker = ticker_store.find_by_stock_code(STOCK_CODE)
    broker = KiwoomBroker()
    collector = ChartCollector()

    yield ticker, broker, collector


def test_proceed_new_ticker(setup):
    ticker, broker, collector = setup

    broker.connect()
    df = collector.proceed_new_ticker(ticker)

    print(tabulate(df.tail(), headers="keys", tablefmt="psql"))
    recent_date = collector.resolve_search_date()
    df_recent_date = df.tail(1).loc[0, 'date']
    assert (recent_date == df_recent_date)


def test_get_recent_chart(setup):
    ticker, broker, collector = setup

    broker.connect()

    """ from_date는 실제로는 DB에서 조회한 최근일자. """
    """ 조회 기준일자 == DB 최근일자이므로 수집할 필요없음 """
    from_date = collector.resolve_search_date()
    df = collector.get_recent_chart(ticker, from_date)
    assert (0 == df.shape[0])

    """ 조회 기준일자를 3일전으로 설정하여 3일치 데이터 수집 확인 """
    date = datetime.strptime(from_date, '%Y%m%d')
    prev_date = date - timedelta(days=3)
    df = collector.get_recent_chart(ticker, prev_date.strftime('%Y%m%d'))
    print(tabulate(df, headers="keys", tablefmt="psql"))
    assert (3 == df.shape[0])


def test_priced_revised(setup, dao):
    ticker, broker, collector = setup

    broker.connect()

    """ 수정종가 발생 조건 테스트"""
    """ 1) 최근 3일치 데이터를 조회해서 DB에 저장 """
    """ 2) 최근 3일치 테이터 중 최초 자료의 종가 수정 """
    """ 수정종가 발생으로 처리되는지 확인 """
    recent_date = collector.resolve_search_date()
    date = datetime.strptime(recent_date, '%Y%m%d')
    prev_date = date - timedelta(days=3)
    df = collector.get_recent_chart(ticker, prev_date.strftime('%Y%m%d'))
    df.sort_values(by="date", inplace=True)
    df = df.reset_index(drop=True)
    dao.insert(ticker.code, df)

    print(tabulate(df, headers="keys", tablefmt="psql"))
    origin_close = df.loc[0, 'close']
    assert not (collector.is_price_revised(df, ticker.code))

    df.loc[0, 'close'] = int(origin_close) - 500
    assert (collector.is_price_revised(df, ticker.code))


