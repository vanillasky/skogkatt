"""
종목코드 조회 테스트시 유의사항
테스트에 사용할 DB와 DAO에 따라서 dao_factory.py 내용 수정 필요

MariaDB로 테스트:
dao_factory = DAOFactory(['conf/maria_dao_conf.yaml'])

MongoDB 테스트시:
dao_factory = DAOFactory(['conf/dao_conf.yaml'])
또는
dao_factory = DAOFactory()

"""
from typing import List

import pandas as pd
import pytest
from tabulate import tabulate

from skogkatt.conf.app_conf import app_config, Config, get_project_path
from skogkatt.core.ticker import Ticker


@pytest.fixture
def ticker_dao(request):
    app_config.set_mode(Config.TEST)

    from skogkatt.core.dao import dao_factory
    from skogkatt.core.dao.idao import TickerDAO
    from skogkatt.tests.core.ticker.ticker_copy import copy_tickers_to

    ticker_dao: TickerDAO = dao_factory.get('TickerDAO')
    """ 테이블이 없거나 테이블에 데이터가 없으면 MongoDB 자료를 복사한다."""
    engine = ticker_dao.get_engine()
    if not engine.exists_table(ticker_dao.get_table_name()) or ticker_dao.count() == 0:
        df = pd.read_excel(get_project_path().joinpath('res/tickers.xlsx'), sheet_name='tickers')
        copy_tickers_to(engine, df)

    def teardown():
        pass

    request.addfinalizer(teardown)

    return ticker_dao


def test_find(ticker_dao):
    count = ticker_dao.count()
    assert (count > 1000)

    df = ticker_dao.find(as_dataframe=True)
    assert (count == df.shape[0])

    count_kospi = ticker_dao.count(market='S')
    tickers_kospi = ticker_dao.find(market='S')
    assert (count_kospi == len(tickers_kospi))

    tickers: List[Ticker] = ticker_dao.find(stock_code="005930")
    assert ("삼성전자", tickers[0].name)


def test_delete_insert(ticker_dao):
    ticker = ticker_dao.find(stock_code="000020")[0]
    assert (ticker is not None)

    deleted = ticker_dao.delete(stock_code='000020')
    assert (1 == deleted)

    inserted = ticker_dao.insert(ticker)
    assert (1 == inserted)


def test_update(ticker_dao):
    df = ticker_dao.find(as_dataframe=True)
    print(tabulate(df, headers="keys", tablefmt="psql"))

    row_count = df.shape[0]

    updated = ticker_dao.update(df)
    assert (row_count, updated)
