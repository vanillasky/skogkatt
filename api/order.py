
from skogkatt.commons.util.numeral import value_of


class Order:
    def __init__(self, account_no=None, ticker=None, quantity=0, price=0, order_type=None,
                 price_type=None, rq_name=None, screen_no=None):
        self._account_no = account_no
        self._ticker = ticker
        self._quantity = quantity
        self._price = price
        self._order_type = order_type
        self._rq_name = rq_name if rq_name is not None else None
        self._screen_no = screen_no if screen_no is not None else None
        self._price_type = price_type if price_type is not None else None

    def __str__(self):
        string_value = '주식주문 [계좌번호:' + self.account_no \
            + ', 종목코드:' + self.ticker \
            + ', 수량:' + str(self.quantity) \
            + ', 단가:' + str(self.price) \
            + ', 매수/매도:' + str(self.order_type) \
            + ', 호가구분:' + value_of(self.price_type)   \
            + ', TR NAME:' + value_of(self.rq_name) \
            + ', 화면번호:' + value_of(self.screen_no) \
            + ']'

        return string_value

    @property
    def account_no(self):
        return self._account_no

    @property
    def ticker(self):
        return self._ticker

    @property
    def quantity(self):
        return self._quantity

    @property
    def price(self):
        return self._price

    @property
    def order_type(self):
        return self._order_type

    @property
    def rq_name(self):
        return self._rq_name

    @property
    def screen_no(self):
        return self._screen_no

    @property
    def price_type(self):
        return self._price_type if self._price_type is not None else 'None'

    @rq_name.setter
    def rq_name(self, rq_name):
        self._rq_name = rq_name

    @screen_no.setter
    def screen_no(self, screen_no):
        self._screen_no = screen_no

    @price_type.setter
    def price_type(self, price_type):
        self._price_type = price_type


class SignedOrder:

    def __init__(self, order, order_no, item_name, undecided_qty, signed_time, sign_no, sign_price, signed_qty):
        self._order = order
        self._order_no = order_no
        self._item_name = item_name
        self._signed_quantity = signed_qty
        self._signed_price = sign_price
        self._signed_time = signed_time
        self._unsigned_quantity = undecided_qty
        self._sign_no = sign_no

    def __str__(self):
        string_value = '체결정보 { 주문: [계좌번호:' + self._order.account_no \
                       + ', 종목코드:' + self._order.ticker \
                       + ', 주문수량:' + str(self._order.quantity) \
                       + ', 주문가격:' + str(self._order.price) \
                       + ', 매수/매도:' + str(self._order.order_type) \
                       + ', 호가구분:' + value_of(self._order.price_type) \
                       + '] 체결 [주문번호:' + self.order_no \
                       + ', 종목명: ' + self.item_name \
                       + ', 체결번호: ' + self.sign_no \
                       + ', 체결수량: ' + self.signed_quantity \
                       + ', 체결가격: ' + self.signed_price \
                       + ', 체결시각: ' + self.signed_time \
                       + ', 미체결수량: ' + self.unsigned_quantity \
                       + '] }'

        return string_value

    @property
    def order_no(self):
        return self._order_no

    @property
    def sign_no(self):
        return self._sign_no

    @property
    def item_name(self):
        return self._item_name

    @property
    def signed_quantity(self):
        return self._signed_quantity

    @property
    def signed_price(self):
        return self._signed_price

    @property
    def signed_time(self):
        return self._signed_time

    @property
    def unsigned_quantity(self):
        return self._unsigned_quantity

    @order_no.setter
    def order_no(self, order_no):
        self._order_no = order_no

    @signed_quantity.setter
    def signed_quantity(self, signed_quantity):
        self._signed_quantity = signed_quantity

    @signed_price.setter
    def signed_price(self, signed_price):
        self._signed_price = signed_price

    @signed_time.setter
    def signed_time(self, signed_time):
        self._signed_time = signed_time

    @unsigned_quantity.setter
    def unsigned_quantity(self, unsigned_quantity):
        self._unsigned_quantity = unsigned_quantity

    @sign_no.setter
    def sign_no(self, sign_no):
        self._sign_no = sign_no

    @item_name.setter
    def item_name(self, item_name):
        self._item_name = item_name

    def get_order(self):
        return self._order
