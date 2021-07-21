import re

from skogkatt.api import EventHandler
from skogkatt.api.account import Account, ItemBalance
from skogkatt.api.kiwoom.constants import TR_RETRIEVE_DEPOSIT, TR_ACCOUNT_BALANCE
from skogkatt.api.kiwoom.event import ApiEvent
from skogkatt.api.kiwoom.rmi import get_comm_data, get_repeat_cnt
from skogkatt.core import LoggerFactory
from skogkatt.commons.util.numeral import to_decimal

logger = LoggerFactory.get_logger(__name__)


class AccountBalanceHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self._account_no = None
        self.account = Account()

    @property
    def account_no(self):
        return self._account_no

    @account_no.setter
    def account_no(self, value):
        self._account_no = value

    def update(self, event: ApiEvent) -> None:
        data = event.data

        if TR_RETRIEVE_DEPOSIT['rq_name'] == data.get('rq_name'):
            self._resolve_deposit_day2(data.get('control'), data.get('rq_name'), data.get('tr_code'))
        elif TR_ACCOUNT_BALANCE['rq_name'] == data.get('rq_name'):
            self._resolve_account_review(data.get('control'), data.get('rq_name'), data.get('tr_code'))

    def get_result(self):
        return {'data': self.account, 'error': None}

    def _resolve_deposit_day2(self, control, rq_name, tr_code):
        d2_deposit = get_comm_data(control, tr_code, rq_name, 0, 'd+2추정예수금')
        self.account.deposit = to_decimal(d2_deposit)
        logger.debug("예수금(d+2) 조회결과: {}".format(to_decimal(d2_deposit)))

    def _resolve_account_review(self, control, rq_name, tr_code):
        self.account.account_no = self._account_no

        self.account.purchase_amount = to_decimal(get_comm_data(control, tr_code, rq_name, 0, "총매입금액"))
        self.account.eval_amount = to_decimal(get_comm_data(control, tr_code, rq_name, 0, "총평가금액"))
        self.account.eval_profit_amount = to_decimal(get_comm_data(control, tr_code, rq_name, 0, "총평가손익금액"))
        self.account.earning_rate = to_decimal(get_comm_data(control, tr_code, rq_name, 0, "총수익률(%)"))
        self.account.estimated_asset = to_decimal(get_comm_data(control, tr_code, rq_name, 0, "추정예탁자산"))

        self.account.owned_items = self._search_owned_items(control, rq_name, tr_code)
        logger.debug('계좌조회 성공: {}'.format(self.account))

    @staticmethod
    def _search_owned_items(control, rq_name, tr_code):
        # logger.debug(f'개별종목평가조회: {tr_code}')
        row_cnt = get_repeat_cnt(control, tr_code, rq_name)
        rows = []

        for i in range(row_cnt):
            item = ItemBalance()
            ticker = re.sub('\\D', '', get_comm_data(control, tr_code, rq_name, i, "종목번호"))
            item.ticker = ticker.strip(' ')

            item_name = get_comm_data(control, tr_code, rq_name, i, "종목명")
            item.item_name = item_name.strip(' ')

            item.quantity = to_decimal(get_comm_data(control, tr_code, rq_name, i, "보유수량"))
            item.purchase_price = to_decimal(get_comm_data(control, tr_code, rq_name, i, "매입가"))
            item.current_price = to_decimal(get_comm_data(control, tr_code, rq_name, i, "현재가"))
            item.eval_profit = to_decimal(get_comm_data(control, tr_code, rq_name, i, "평가손익"))
            item.earning_rate = to_decimal(get_comm_data(control, tr_code, rq_name, i, "수익률(%)"))
            logger.debug(f'종목별현황: {item}')
            rows.append(item)

        return rows

# class AccountReviewHandler:
#     """
#     예수금상세현황, 계좌평가잔고내역요청 조회 결과 처리
#     """
#     def __init__(self, account_no=None):
#         self.account = Account(account_no=account_no)
#         self.required_arguments = ('api', 'rq_name', 'tr_code')
#         self.err_message = None
#
#     def check_arguments(self, args):
#         for arg in self.required_arguments:
#             if arg not in args:
#                 raise AttributeError(f'Missing Argument: {arg}')
#
#     def handle(self, **kwargs):
#         self.check_arguments(kwargs)
#
#         if TR_RETRIEVE_DEPOSIT['rq_name'] == kwargs['rq_name']:
#             self._handle_deposit_d2(kwargs['api'], kwargs['rq_name'], kwargs['tr_code'])
#         elif TR_ACCOUNT_BALANCE['rq_name'] == kwargs['rq_name']:
#             self._handle_account_review(kwargs['api'], kwargs['rq_name'], kwargs['tr_code'])
#
#     def get_result(self):
#         return {'result': self.account, 'error_message': None}
#
#     def _handle_deposit_d2(self, api, rq_name, tr_code):
#         d2_deposit = get_comm_data(api, tr_code, rq_name, 0, 'd+2추정예수금')
#         logger.debug("예수금(d+2) 조회결과: {}".format(d2_deposit))
#         self.account.deposit = to_decimal(d2_deposit)
#
#     def _handle_account_review(self, api, rq_name, tr_code):
#         self.account.purchase_amount = to_decimal(get_comm_data(api, tr_code, rq_name, 0, "총매입금액"))
#         self.account.eval_amount = to_decimal(get_comm_data(api, tr_code, rq_name, 0, "총평가금액"))
#         self.account.eval_profit_amount = to_decimal(get_comm_data(api, tr_code, rq_name, 0, "총평가손익금액"))
#         self.account.earning_rate = to_decimal(get_comm_data(api, tr_code, rq_name, 0, "총수익률(%)"))
#         self.account.estimated_asset = to_decimal(get_comm_data(api, tr_code, rq_name, 0, "추정예탁자산"))
#
#         self.account.owned_items = self._search_owned_items(api, rq_name, tr_code)
#         logger.debug('AccountReview created: {}'.format(self.account))
#
#     @staticmethod
#     def _search_owned_items(api, rq_name, tr_code):
#         logger.debug(f'개별종목평가조회: {tr_code}')
#         row_cnt = get_repeat_cnt(api, tr_code, rq_name)
#         rows = []
#
#         for i in range(row_cnt):
#             item = ItemBalance()
#             ticker = re.sub('\\D', '', get_comm_data(api, tr_code, rq_name, i, "종목번호"))
#             item.ticker = ticker.strip(' ')
#
#             item_name = get_comm_data(api, tr_code, rq_name, i, "종목명")
#             item.item_name = item_name.strip(' ')
#
#             item.quantity = to_decimal(get_comm_data(api, tr_code, rq_name, i, "보유수량"))
#             item.purchase_price = to_decimal(get_comm_data(api, tr_code, rq_name, i, "매입가"))
#             item.current_price = to_decimal(get_comm_data(api, tr_code, rq_name, i, "현재가"))
#             item.eval_profit = to_decimal(get_comm_data(api, tr_code, rq_name, i, "평가손익"))
#             item.earning_rate = to_decimal(get_comm_data(api, tr_code, rq_name, i, "수익률(%)"))
#             logger.debug(f'종목별현황: {item}')
#             rows.append(item)
#
#         return rows
