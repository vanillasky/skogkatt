import sys
import time
from typing import List

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

from skogkatt.api import Broker
from skogkatt.api.kiwoom import rmi
from skogkatt.api.kiwoom.constants import (
    TR_SEND_ORDER, NEXT, PARAM_ACCOUNT_NO, TR_ACCOUNT_BALANCE,
    TR_REQ_TIME_INTERVAL, TR_RETRIEVE_DEPOSIT,
    TR_DAILY_STOCK_CHART, TR_CONDITIONAL_SEARCH, COND_SEARCH_CONT, COND_SEARCH_DEFAULT, RT_CURRENT_PRICE
)
from skogkatt.api.kiwoom import error_message
from skogkatt.api.kiwoom.event import (
    ConnectEvent, TrDataEvent, OrderSignedEvent, FilterFormulaLoadEvent,
    ReceiveFilteredEvent, RealTimeDataEvent
)
from skogkatt.api.kiwoom.handler.account import AccountBalanceHandler
from skogkatt.api.kiwoom.handler.chart import DailyChartHandler
from skogkatt.api.kiwoom.handler.screener import FormulaLoadEventHandler, ConditionalStockHandler
from skogkatt.api.kiwoom.handler.login import LoginEventHandler
from skogkatt.api.kiwoom.handler.message import ServerMessage
from skogkatt.api.kiwoom.handler.order import OrderSignedHandler
from skogkatt.api.trader import Trader

from skogkatt.conf.app_conf import app_config
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class KiwoomBroker(Broker):

    def __init__(self, login=False):
        self._control = QAxWidget(app_config.get("KIWOOM_CONTROL"))
        self._init_event_slot()

        self.login_event: ConnectEvent = ConnectEvent()
        self.tr_event: TrDataEvent = TrDataEvent()
        self.order_signed_event: OrderSignedEvent = OrderSignedEvent()
        self.formula_load_event = FilterFormulaLoadEvent()
        self.receive_filtered_event = ReceiveFilteredEvent()
        self.realtime_data_event = RealTimeDataEvent()

        self.message = ServerMessage()

        self._tr_remained = False  # 처리할 TR이 남아있는지 여부
        # self.rq_count = 0  # API TR 호출 횟수
        # self.handler_map = {}

    def _init_event_slot(self):

        """
        키움 Open API 이벤트 연결
        """
        try:
            self._control.OnEventConnect.connect(self.on_event_connect)
            self._control.OnReceiveMsg.connect(self.on_receive_msg)
            self._control.OnReceiveTrData.connect(self.on_receive_tr_data)
            self._control.OnReceiveRealData.connect(self.on_receive_real_data)
            self._control.OnReceiveChejanData.connect(self.on_receive_chejan_data)
            self._control.OnReceiveConditionVer.connect(self.on_receive_condition_ver)
            self._control.OnReceiveTrCondition.connect(self.on_receive_tr_condition)
            # self._control.OnReceiveRealCondition.connect(self.on_receive_real_condition)

        except (Exception, AttributeError) as e:
            print(e)
            is_64bits = sys.maxsize > 2 ** 32
            if is_64bits:
                logger.critical(
                    'Current Anaconda is running on 64bit environment. 32bit environment is required for Kiwoom.')
                sys.exit(-1)
            else:
                logger.error(str(e))

    def _wait_for_response(self):
        self._control.tr_event_loop = QEventLoop()
        self._control.tr_event_loop.exec_()

    def _response_received(self):
        self._control.tr_event_loop.exit()

    def _set_input_values(self, params):
        # 요청시 필요한 입력데이터 세팅
        for key, val in params.items():
            rmi.set_input_value(self._control, key, val)

    def _request_tr(self, tran, _next=None):
        """
        Tran을 서버로 전송한다.
        :param tran: Tran 정보를 담고있는 dictionary
            ex) {'rq_name': 'opt10081_req', 'tr_code': 'opt10081', 'tr_name': '주식일봉차트조회요청', 'screen_no': '2001'}
        :param _next: 0: 조회, 1:연속
        :return:
            OP_ERR_SISE_OVERFLOW – 과도한 시세조회로 인한 통신불가
            OP_ERR_RQ_STRUCT_FAIL – 입력 구조체 생성 실패
            OP_ERR_RQ_STRING_FAIL – 요청전문 작성 실패
            OP_ERR_NONE – 정상처리
        """
        search_next = _next if _next is not None else 0
        status = rmi.comm_rq_data(self._control, tran['rq_name'], tran['tr_code'], search_next, tran['screen_no'])

        if status < 0:
            raise RuntimeError(error_message(status))

        time.sleep(TR_REQ_TIME_INTERVAL)
        self._wait_for_response()

    """ ------------------------------------------------------------------ """
    """ ------------------------- Sever Events  -------------------------- """
    """ ------------------------------------------------------------------ """
    def on_receive_msg(self, screen_no, rq_name, tr_code, msg):
        logger.debug(f'screen:{screen_no}, rq_name:{rq_name}, tr_code:{tr_code}, msg:{msg}')
        self.message.update(screen_no=screen_no, rq_name=rq_name, tr_code=tr_code, msg=msg)

    def on_event_connect(self, err_code):
        """
        서버 접속 이벤트 처리
        :param err_code: 0: 접속성공, 음수: 접속실패
        :return:
        """
        self._control.login_event_loop.exit()
        self.login_event.fire_event(err_code)

    def on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, _next):
        """
        Tran 수신시 이벤트 처리
        :param screen_no: 화면번호
        :param rq_name: 사용자 구분용 request name
        :param tr_code: Tran 코드
        :param record_name: 레코드명
        :param _next: 연속조회 유무 - 0:없음, 2:연속조회 있음
        :return: no return value
        """
        logger.debug(f"screen_no:{screen_no}, rq_name: {rq_name}, tr_code: {tr_code}, next: {_next}")
        # 주문전송 후 OnReceiveTrData는 처리하지 않는다
        if TR_SEND_ORDER.get("rq_name") == rq_name:
            return

        self._response_received()
        self._tr_remained = True if _next and NEXT == int(_next) else False

        self.tr_event.fire_event(control=self._control,
                                 screen_no=screen_no,
                                 rq_name=rq_name,
                                 tr_code=tr_code,
                                 record_name=record_name,
                                 search_next=_next)

    def on_receive_chejan_data(self, sign_type, item_cnt, fid_list):
        """
        주문 접수/확인 수신시 이벤트 OnReceiveChejanData 처리
        :param sign_type: 체결구분 [0: 주문체결통보, 1: 국내주식 잔고통보, 4: 파생상품 잔고통보]
        :param item_cnt: 아이템개수
        :param fid_list: 데이터리스트
        :return:
        """
        logger.debug(f"sign_type: {sign_type}, item_cnt: {item_cnt}")
        self._response_received()
        self.order_signed_event.fire_event(control=self._control, sign_type=sign_type, item_cnt=item_cnt, fid_list=fid_list)

    def on_receive_condition_ver(self, result: int, msg):
        """ 조건검색 로드 이벤트 처리 """
        self._response_received()
        if result == 0:
            logger.error("조건검색 로드 실패")
            raise RuntimeError("조건검색 로드 실패")

        condition_str = rmi.get_condition_list(self._control)
        """ ex) 조건인덱스1^조건명1;조건인덱스2^조건명2; """
        conditions = condition_str.split(';')[:-1]
        self.formula_load_event.fire_event(conditions=conditions)

    def on_receive_tr_condition(self, screen_no, code_list, cond_name, cond_index, _next):
        """
        조건건색에 해당하는 종목 리스트를 볼러왔을 때.
        :param screen_no: str, 화면번호
        :param code_list: str, 종목코드. ";" separated
        :param cond_name: str, 조건검색명
        :param cond_index: str, 조건건색 인덱스
        :param _next: int, 남은 항목 여부. 2이면 추가조회
        :return:
        """
        logger.debug(f'next: {_next}, code_list: {code_list}')
        self._response_received()

        self._tr_remained = True if _next and NEXT == int(_next) else False
        self.receive_filtered_event.fire_event(code_list=code_list,
                                               cond_name=cond_name,
                                               cond_index=cond_index)

    def on_receive_real_data(self, stock_code, real_type, data):
        """
        실시간 데이터 수신 이벤트
        :param stock_code: str, 종목코드
        :param real_type: str, 실시간 타입
        :param data: str, 실시간 데이터 전문
        :return:
        """
        logger.debug(f'실시간 데이터 수신 stock_code: {stock_code}, type: {real_type}, data: {data}')

        if real_type == "주식체결":
            # print(f"sCode: {s_code}, sRealType: {s_real_type}, sRealData: {s_real_data}")
            price = rmi.get_comm_real_data(self._control, stock_code, 10)
            print(f"sCode: {stock_code}, price: {price}")
            # self._control.tr_event_loop.exit()

            # self._response_received()

            self.realtime_data_event.fire_event(stock_code=stock_code, real_type=real_type, real_data=data, price=price)

    """ ------------------------------------------------------------------ """
    """ ------------------------- API Functions -------------------------- """
    """ ------------------------------------------------------------------ """
    def get_connect_state(self):
        """
        현재접속상태를 반환한다.
        :param api:
        :return: 0: 미연결, 1: 연결완료
        """
        return rmi.get_connect_state(self._control)

    def connect(self, block=True):
        """
        로그인 윈도우 실행.
        :param block: True: 로그인 완료까지 블록킹 됨, False: 블록킹 하지 않음
        """
        handler = LoginEventHandler()
        self.login_event.register(handler)
        rmi.connect(self._control)
        if block:
            self._control.login_event_loop = QEventLoop()
            self._control.login_event_loop.exec_()

        return handler.get_result()

    def get_server_type(self) -> str:
        """
        서버구분을 반환한다. 1: 모의투자, 나머지: 실서버
        :return:
        """
        return rmi.get_server_type(self._control)

    def get_user_id(self) -> str:
        return rmi.get_login_info(self._control, 'USER_ID')

    def get_accounts(self) -> List[str]:
        """
        보유 계좌 목록반환
        :return:
            List[str]
        """
        accounts = rmi.get_login_info(self._control, 'ACCNO').split(";")
        if len(accounts) > 2:
            return accounts[0:-2]
        else:
            return [accounts[0]]

    def account_balance(self, account_no):
        """
        계좌평가 잔고내역 조회
        :return:
        """
        handler = AccountBalanceHandler()
        handler.account_no = account_no
        self.tr_event.register(handler)

        rmi.set_input_value(self._control, "계좌번호", account_no)
        self._request_tr(TR_ACCOUNT_BALANCE)

        while self._tr_remained:
            rmi.set_input_value(self._control, "계좌번호", account_no)
            self._request_tr(TR_ACCOUNT_BALANCE, NEXT)

        self.get_deposit_day2(account_no)

        self.tr_event.remove(handler)
        return handler.get_result()

    def get_deposit_day2(self, account_no):
        """
        예수금 정보 조회
        :param account_no:
        :return:
        """
        logger.debug(f'D+2 예수금 조회 요청 - 계좌번호 {account_no}')
        rmi.set_input_value(self._control, PARAM_ACCOUNT_NO, account_no)
        self._request_tr(TR_RETRIEVE_DEPOSIT)

    def get_chart(self, stock_code: str, date: str, search_next=None, limit=None):
        """
        일봉데이터 조회
        :param stock_code: str, 종목코드
        :param date: str, 기준일자
        :param search_next: 연속 조회 여부
        :param limit: loop count
        :return: DataFrame - 일봉데이타
        """
        _search_next = search_next if search_next is not None else True
        _limit = None if limit is None else limit

        handler = DailyChartHandler()
        handler.limit = _limit
        self.tr_event.register(handler)

        params = {'종목코드': stock_code, '기준일자': date, '수정주가구분': 1}
        self._set_input_values(params)
        self._request_tr(TR_DAILY_STOCK_CHART)

        while self._tr_remained and _search_next:
            # self._check_tr_call_count()
            params = {'종목코드': stock_code, '기준일자': date, '수정주가구분': 1}
            self._set_input_values(params)
            self._request_tr(TR_DAILY_STOCK_CHART, NEXT)

        self.tr_event.remove(handler)
        return handler.get_result()

    def send_order(self, order):
        """
        주문 전송
        :param order: Order, 주문 데이타
        :return:
            SignedOrder object
        """
        if not Trader.is_market_opened():
            raise RuntimeError("주문 가능 시각이 아닙니다.")

        logger.debug(f"Send Order: {order}")
        handler = OrderSignedHandler(order)
        self.order_signed_event.register(handler)
        # self.tr_event.register(handler)

        status = rmi.send_order(api=self._control,
                                rq_name=TR_SEND_ORDER['rq_name'],
                                screen_no=TR_SEND_ORDER['screen_no'],
                                acc_no=order.account_no,
                                order_type=order.order_type,
                                code=order.ticker,
                                quantity=order.quantity,
                                price=order.price,
                                price_type=order.price_type)

        if status is not None and status < 0:
            raise RuntimeError(error_message(status))

        self._wait_for_response()
        self.order_signed_event.remove(handler)
        # self.tr_event.remove(handler)

        return handler.get_result()

    def get_filter_formulas(self):
        """ 조건검색 목록을 조회한다 """
        handler = FormulaLoadEventHandler()
        self.formula_load_event.register(handler)

        rmi.load_condition(self._control)
        self._wait_for_response()
        self.formula_load_event.remove(handler)

        return handler.get_result()

    def get_filtered_tickers(self, index: str, name: str, search_next=None):
        handler = ConditionalStockHandler()
        self.receive_filtered_event.register(handler)

        _search_next = search_next if search_next is not None else True

        status = rmi.send_condition(self._control, TR_CONDITIONAL_SEARCH['screen_no'], name, index, COND_SEARCH_DEFAULT)
        logger.debug(f'Search conditional stocks - Return:{status}, 조건건색 인덱스:{index}, 조건검색명: {name}')
        self._wait_for_response()

        while self._tr_remained and _search_next:
            status = rmi.send_condition(self._control, TR_CONDITIONAL_SEARCH['screen_no'], name, index, COND_SEARCH_CONT)
            logger.debug(f'Search conditional stocks - Return:{status}, 조건건색 인덱스:{index}, 조건검색명: {name}')
            time.sleep(TR_REQ_TIME_INTERVAL)
            self._wait_for_response()

        self.receive_filtered_event.remove(handler)
        return handler.get_result()

    def get_current_price(self, stock_codes: List[str]):

        if len(stock_codes) > 100:
            raise ValueError('실시간 종목은 100개 까지만 등록이 가능합니다.')

        status = rmi.register_realtime(self._control, stock_codes, RT_CURRENT_PRICE)

        self._wait_for_response()

