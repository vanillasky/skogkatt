
class Account:
    def __init__(self, **kwargs):

        self.account_no = kwargs.get('account_no', None)
        self.deposit = kwargs.get('deposit', 0)
        self.purchase_amount = kwargs.get('purchase_amount', 0)
        self.eval_amount = kwargs.get('eval_amount', 0)
        self.eval_profit_amount = kwargs.get('eval_profit_amount', 0)
        self.earning_rate = kwargs.get('earning_rate', 0)
        self.estimated_asset = kwargs.get('estimated_asset', 0)
        self.owned_items = None

    def __str__(self):
        string_value = '[계좌번호: ' + str(self.account_no) \
                       + ', 예수금(d+2): ' + str(self.deposit) \
                       + ', 총매입금액:' + str(self.purchase_amount) \
                       + ', 총평가금액:' + str(self.eval_amount) \
                       + ', 총평가손익금액:' + str(self.eval_profit_amount) \
                       + ', 총수익률:' + str(self.earning_rate) \
                       + ', 추정예탁자산:' + str(self.estimated_asset) + ']'
        return string_value

    def get_item(self, ticker=None, name=None):
        if ticker is None and name is None:
            return None

        if self.owned_items is None or len(self.owned_items) == 0:
            return None

        for item in self.owned_items:
            if ticker is not None:
                if item.ticker == ticker:
                    return item
            elif name is not None:
                if item.item_name == name:
                    return item
            return None


class ItemBalance:
    def __init__(self):
        self.ticker = None
        self.item_name = None
        self.quantity = None
        self.purchase_price = None
        self.current_price = None
        self.eval_profit = None
        self.earning_rate = None

    def __str__(self):
        string_value = '[종목코드:' + self.ticker \
            + ', 종목명:' + self.item_name \
            + ', 보유수량:' + str(self.quantity) \
            + ', 매입가:' + str(self.purchase_price) \
            + ', 현재가:' + str(self.current_price) \
            + ', 평가손익:' + str(self.eval_profit) \
            + ', 수익률(%):' + str(self.earning_rate) + ']'

        return string_value
