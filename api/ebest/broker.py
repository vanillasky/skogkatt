import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pythoncom
from win32com.client import DispatchWithEvents

from skogkatt.api.ebest import tr_factory
from skogkatt.api.ebest.event import ConnectEvent, XAQueryEvent

from skogkatt.api import Broker
from skogkatt.api.ebest.handler.account import AccountBalanceHandler
from skogkatt.api.ebest import QueryBuilder
from skogkatt.api.ebest.handler.chart import DailyChartHandler
from skogkatt.api.ebest.handler.login import LoginEventHandler
from skogkatt.api.ebest.handler.screener import FilterFormulaHandler
from skogkatt.conf.app_conf import app_config
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class EBestBroker(Broker):

    TIMER = {}

    def __init__(self):
        self.session = None
        self._accounts = []

        """ 조건검색 ACF 파일 경로"""
        self.acf_dir = os.path.abspath(app_config.get("EBEST_ACF_DIR"))

    def get_server_type(self):
        pass

    def get_accounts(self):
        if self.session is None:
            self.connect()

        return self._accounts

    def get_user_id(self) -> str:
        pass

    def get_account_balance(
            self,
            account_no,
            password,
            price_type='1',
            sign_type='0',
            out_of_hour='0',
            include_cost='1',
            cts_code=''):
        """
        주식잔고 조회
        :param account_no: 계좌번호
        :param password: 계좌 비밀번호
        :param price_type: 단가구분, 1:평균단가, 2:BEP단가
        :param sign_type: 체결구분, 0: 결제기준 잔고, 2: 체결기준
        :param out_of_hour: 단일가 구분, 0:정규장, 1:시간외단일가
        :param include_cost: 제비용포함여부, 0:미포함, 1: 포함
        :param cts_code: 처음 조회시 space, 연속조회시 이전 조회한 OutBlock의 ctx_code 값
        :return:
            dict {data:Account, error: error_code}
        """
        handler = AccountBalanceHandler(account_no)
        query = DispatchWithEvents("XA_DataSet.XAQuery", XAQueryEvent)
        query.register(handler)

        builder = QueryBuilder(query, tr_factory.get("주식잔고2"))
        query = builder.build(account_no, password, price_type, sign_type, out_of_hour, include_cost, cts_code)
        query.Request(0)
        query.wait_for_response()
        query.remove(handler)

        return handler.get_result()

    def get_chart(self, stock_code=None, period_type='1', date=None, cnt=900, idx='', cont_search=False, handlers=[]):
        transaction = tr_factory.get("기간별주가")
        self.check_and_wait_interval(transaction.tr_code)

        if len(handlers) == 0:
            handlers.append(DailyChartHandler())

        query = DispatchWithEvents("XA_DataSet.XAQuery", XAQueryEvent)
        [query.register(handle) for handle in handlers]

        builder = QueryBuilder(query, transaction)
        query = builder.build(stock_code, period_type, date, idx, cnt)
        query.Request(0)
        query.wait_for_response()
        query.clear()

        if len(handlers) == 1:
            return handlers[0].get_result()
        else:
            return handlers

    def send_order(self, order):
        pass

    def get_filter_formulas(self):
        return os.listdir(self.acf_dir)

    def get_filtered_tickers(self, filter_name, real_flag='0', search_flag='F', handlers=[]):
        transaction = tr_factory.get("조건검색")
        # self.check_and_wait_interval(transaction.tr_code)

        if len(handlers) == 0:
            handlers.append(FilterFormulaHandler())

        query = DispatchWithEvents("XA_DataSet.XAQuery", XAQueryEvent)

        [query.register(handle) for handle in handlers]

        dir_path = Path(os.path.abspath(self.acf_dir))
        acf_file = dir_path.joinpath(filter_name)

        if not os.path.exists(acf_file):
            raise FileNotFoundError(acf_file)

        builder = QueryBuilder(query, transaction)
        query = builder.build(real_flag, search_flag, acf_file)
        query.RequestService(transaction.tr_code, "")
        query.wait_for_response()
        query.clear()

        if len(handlers) == 1:
            return handlers[0].get_result()
        else:
            return handlers

    def get_current_price(self, stock_codes: List[str]):
        pass
        # # if self.session is None:
        # self.connect()
        #
        # query = DispatchWithEvents("XA_DataSet.XAQuery", XAQueryEventHandler)
        # query.ResFileName = 'C:\\eBEST\\xingAPI\\Res\\t1102.res'
        # query.SetFieldData("t1102InBlock", "sRealFlag", 0, "005930")
        # query.Request(0)
        #
        # while XAQueryEventHandler.query_state == 0:
        #     pythoncom.PumpWaitingMessages()
        #
        # name = query.GetFieldData('t1102OutBlock', 'hname', 0)
        # price = query.GetFieldData('t1102OutBlock', 'price', 0)
        #
        # return {'data': {'name': name, 'price': price}, 'error': None}

    def get_connect_state(self):
        return True if self.session is not None else False

    def connect(self, block=True):
        self.session = DispatchWithEvents("XA_Session.XASession", ConnectEvent)
        # self.session.SetMode("_XINGAPI7_", "TRUE")
        result = self.session.ConnectServer(app_config.get("EBEST_HOST"), int(app_config.get("EBEST_HOST_PORT")))

        handler = LoginEventHandler()
        self.session.register(handler)

        if not result:
            err_code = self.session.GetLastError()
            err_message = self.session.GetErrorMessage(err_code)
            return {'data': err_code, 'error': err_message}

        self.session.Login(app_config.get('EBEST_USER_ID'),
                           app_config.get('EBEST_PASSWD'),
                           app_config.get('CERT_PASS'), 0, 0)

        self.session.wait_for_response()

        num_account = self.session.GetAccountListCount()
        logger.debug(f'Logged in Successfully, You have {num_account} account(s).')
        for i in range(num_account):
            self._accounts.append(self.session.GetAccountList(i))

        return handler.get_result()

    def check_and_wait_interval(self, tr_code):
        now = datetime.now()
        interval = timedelta(milliseconds=2000)

        elapsed = EBestBroker.TIMER.get(tr_code, None)

        if elapsed is None:
            EBestBroker.TIMER[tr_code] = now + interval
        else:
            if now > elapsed:
                print(now, elapsed)
                EBestBroker.TIMER[tr_code] = now + interval
            else:
                diff = (elapsed - now).total_seconds()
                print(f'Sleep {diff}')
                time.sleep(diff)
                now = datetime.now()
                EBestBroker.TIMER[tr_code] = now + interval
