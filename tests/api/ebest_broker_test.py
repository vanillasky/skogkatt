import sys
import time

import pytest
from PyQt5.QtWidgets import QApplication
from tabulate import tabulate

from skogkatt.api import EventHandler, ApiEvent
from skogkatt.commons.util.numeral import to_decimal
from skogkatt.conf.app_conf import app_config


class HandlerSample(EventHandler):

    def update(self, event: ApiEvent) -> None:
        print("Update with event")
        self.data = event.data['tr_code']

    def some_business_logic(self):
        print("Do something with data from event")
        print(self.data)

    def get_result(self):
        return {'data': self.data['tr_code'], 'error': None}


@pytest.fixture
def q_app():
    app = QApplication(sys.argv)

    yield app


@pytest.fixture
def setup(q_app, request):
    from skogkatt.api.ebest.broker import EBestBroker

    broker = EBestBroker()

    yield broker


def test_connect(setup):
    broker = setup
    data, err_code, message = broker.connect()
    assert (0 == err_code)


def test_get_accounts(setup):
    broker = setup
    accounts = broker.get_accounts()
    print(accounts)


def test_account_balance_error(setup):
    broker = setup
    broker.connect()

    account, err_code, message = broker.account_balance("3" + app_config.get("EBEST_ACCOUNT_NO"), app_config.get("EBEST_ACCOUNT_PASSWD"))
    print(message)
    assert (err_code == -9)


def test_account_balance(setup):
    broker = setup
    broker.connect()
    account, err_code, message = broker.get_account_balance(app_config.get("EBEST_ACCOUNT_NO"), app_config.get("EBEST_ACCOUNT_PASSWD"))
    assert account.account_no == app_config.get("EBEST_ACCOUNT_NO")
    print(account)


def test_get_filter_formula(setup):
    """  조건검색식 목록"""
    broker = setup
    broker.connect()
    acf_files = broker.get_filter_formulas()
    assert 1 < len(acf_files)


def test_filtered_tickers(setup):
    """ 조건검색 with Default Handler """
    broker = setup
    broker.connect()
    data, err_code, message = broker.get_filtered_tickers('볼린저_상한선_상향돌파.ACF')
    time.sleep(1)
    data, err_code, message = broker.get_filtered_tickers('윌리엄오닐.ACF')


def test_filter_formula_with_handler(setup):
    """  조건검색 with 별도 핸들러 """
    broker = setup
    broker.connect()
    handler = HandlerSample()
    broker.get_filtered_tickers(handlers=[handler])
    handler.some_business_logic()
    data, err_code, message = handler.get_result()
    assert 't1857' == data


def test_get_chart(setup):
    """ t1305 기간별 주가"""
    broker = setup
    broker.connect()
    stock_code = "005930"
    period_type = "1"    # 일, 주 월: 1, 2, 3
    date = ""
    cnt = 20
    cont_search = True
    df, err_code, message = broker.get_chart(stock_code, period_type, date, cnt, cont_search)
    assert err_code == 0
    assert df.shape[0] == cnt
    print(tabulate(df, headers="keys", tablefmt="psql"))


