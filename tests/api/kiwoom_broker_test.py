import sys
import time
from typing import List

import pytest
from PyQt5.QtWidgets import QApplication
from tabulate import tabulate

from skogkatt.api.kiwoom.constants import PRICE_TYPES, ORDER_TYPES
from skogkatt.api.kiwoom.handler.screener import FilterFormula
from skogkatt.api.order import Order
from skogkatt.api.trader import Trader
from skogkatt.conf.app_conf import app_config, Config

""" 메소드별로 테스트 필요. 일괄 실행시 QEventLoop 때문에 에러발생하는 것으로 보임. 미해결 상태 """

app_config.set_mode(Config.TEST)


@pytest.fixture
def q_app():
    app = QApplication(sys.argv)

    yield app


@pytest.fixture
def setup(q_app, request):
    from skogkatt.api.kiwoom.broker import KiwoomBroker

    broker = KiwoomBroker()

    yield broker


def test_connect(setup):
    broker = setup
    result = broker.connect()
    assert (0 == int(result['data']))


def test_get_server_type(setup):
    broker = setup
    broker.connect()
    """ 모의투자: 1, 나머지: 실서버 """
    server_type = broker.get_server_type()
    assert (1 == int(server_type))


def test_get_login_info(setup):
    broker = setup
    broker.connect()

    user_id = broker.get_user_id()
    assert (user_id is not None)

    accounts = broker.get_accounts()
    assert (accounts[0] is not None)


def test_get_user_id(setup):
    broker = setup
    broker.connect()

    user_id = broker.get_user_id()
    assert (user_id is not None)

    accounts = broker.get_accounts()
    assert (accounts[0] is not None)


def test_account_review(setup):
    broker = setup
    broker.connect()

    accounts = broker.get_accounts()
    result = broker.account_balance(accounts[0])

    assert (result['error'] is None)

    env_account_no = app_config.get("KIWOOM_MOCK_ACCOUNT_NO")
    account = result['data']
    assert (env_account_no, account.account_no)
    print(account)
    for item in account.owned_items:
        print(item)


def test_get_chart(setup):
    broker = setup
    broker.connect()
    result = broker.get_chart('005930', '20000101')
    df = result.get('data')
    print(tabulate(df.tail(), headers="keys", tablefmt="psql"))
    assert (result.get('error') is None)
    assert (100 < df.shape[0])
    assert (6, df.shape[1])


def test_buy_order(setup):
    broker = setup
    broker.connect()

    if not Trader.is_market_opened():
        print("주문 가능 시각이 아니므로 테스트 실행 안함")
        return

    # 현재 보유 주식 확인
    account_no = broker.get_accounts()[0]
    account = broker.account_balance(account_no).get('data')
    owned_item = account.get_item(ticker='005930')
    current_qty = 0
    if owned_item is not None:
        current_qty = owned_item.quantity
        # print(owned_item.quantity, type(owned_item.quantity))

        #  주문전송
        order = Order(account_no=account_no,
                      ticker="005930",
                      quantity=1,
                      price_type=PRICE_TYPES['시장가'],
                      order_type=ORDER_TYPES['매수'])

        result = broker.send_order(order)
        signed_order = result.get('data')
        assert ("삼성전자" == signed_order.item_name)

        time.sleep(3)
        account = broker.account_balance(account_no).get('data')
        item = account.get_item(ticker='005930')
        assert (item.quantity == current_qty+1)


def test_condition_search(setup):
    broker = setup
    broker.connect()

    conditions: List[FilterFormula] = broker.get_filter_formulas().get('data')
    assert (0 < len(conditions))
    for each in conditions:
        print(each)

    condition: FilterFormula = broker.get_filtered_tickers(conditions[0].index, conditions[0].name).get('data')
    print(condition)
#
#     def test_real_time_price(self):
#         self.broker.connect()
#         self.broker.get_current_price(['035720', '005930'])
#
#
