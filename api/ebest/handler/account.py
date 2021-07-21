import re

from skogkatt.api import EventHandler, ApiEvent, Account
from skogkatt.api.account import ItemBalance
from skogkatt.commons.util.numeral import to_decimal
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class AccountBalanceHandler(EventHandler):
    def __init__(self, account_no):
        super().__init__()
        self.account = None
        self._account_no = account_no
        self.out_block = "t0424OutBlock"
        self.out_block1 = "t0424OutBlock1"

    def update(self, event: ApiEvent) -> None:
        if event.error_code != 0:
            self._error_code = event.error_code
            self._message = event.message
            return

        data = event.data
        xa_query = data.get('query')

        if xa_query is None:
            raise RuntimeError('xa_query should not be None')

        self._resolve_account(xa_query)
        self._data = self.account
        self._error_code = None

    def _resolve_account(self, xa_query):
        self.account = Account(account_no=self._account_no)

        cnt = xa_query.GetBlockCount(self.out_block)
        for i in range(cnt):
            self.account.estimated_asset = to_decimal(xa_query.GetFieldData(self.out_block, "sunamt", i))
            # self.account.eval_profit_amount = to_decimal(xa_query.GetFieldData(self.out_block, "dtsunik", i))
            self.account.purchase_amount = to_decimal(xa_query.GetFieldData(self.out_block, "mamt", i))
            self.account.deposit = to_decimal(xa_query.GetFieldData(self.out_block, "sunamt1", i))
            # CTS_종목번호 = xa_query.GetFieldData(outblock, "cts_expcode", i).strip()
            self.account.eval_amount = to_decimal(xa_query.GetFieldData(self.out_block, "tappamt", i))
            self.account.eval_profit_amount = to_decimal(xa_query.GetFieldData(self.out_block, "tdtsunik", i))

        self.account.owned_items = self._get_item_balance(xa_query)

    def _get_item_balance(self, xa_query):
        stock_cnt = xa_query.GetBlockCount(self.out_block1)
        rows = []
        sum_profit_rate = 0

        for i in range(stock_cnt):
            item = ItemBalance()
            item.ticker = re.sub('\\D', '', xa_query.GetFieldData(self.out_block1, "expcode", i).strip())
            item.item_name = xa_query.GetFieldData(self.out_block1, "hname", i).strip()
            item.quantity = to_decimal(xa_query.GetFieldData(self.out_block1, "janqty", i).strip())
            item.purchase_price = to_decimal(xa_query.GetFieldData(self.out_block1, "pamt", i).strip())
            item.current_price = to_decimal(xa_query.GetFieldData(self.out_block1, "price", i).strip())
            item.eval_profit = to_decimal(xa_query.GetFieldData(self.out_block1, "dtsunik", i).strip())
            item.earning_rate = to_decimal(xa_query.GetFieldData(self.out_block1, "sunikrt", i).strip())
            logger.debug(f'종목별현황: {item}')
            sum_profit_rate += item.earning_rate
            rows.append(item)

        self.account.earning_rate = sum_profit_rate
        return rows

