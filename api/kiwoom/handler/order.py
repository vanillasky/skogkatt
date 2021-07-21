from skogkatt.api import EventHandler
from skogkatt.api.kiwoom.constants import FID_ORDER_NO, FID_ITEM_NAME, FID_SETTLEMENT_QTY, FID_SETTLEMENT_PRICE, \
    FID_SETTLEMENT_TIME, FID_UNDECIDED, FID_SETTLEMENT_NO
from skogkatt.api.kiwoom import error_message
from skogkatt.api.kiwoom.event import ApiEvent
from skogkatt.api.kiwoom.rmi import get_order_sign_data
from skogkatt.api.order import SignedOrder
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class OrderSignedHandler(EventHandler):
    """
    주식 주문시 체결잔고 데이터 처리.
    주문 전송 후에는 체결잔고 데이터를 받는 OnReceiveChejanData 이벤트와 OnReceiveTrData 이벤트가 모두 발생헐 수 있다.
    장중에 주문을 전송하면 둘 다 발생, 장종료 때 주문 전송하면 OnReceiveTrData 이벤트만 발생.
    주문전송 후 OnReceiveTrData는 일단 오류로 간주하고 OnReceiveChejanData 이벤트를 처리할 때 정상인 것으로 처리
    """
    def __init__(self, order):
        super().__init__()
        self.order = order
        self.signed_order = None

    def update(self, event: ApiEvent) -> None:
        data = event.data
        control = data.get('control')
        logger.debug(f"체결잔고 데이터 수신: 체결구분: {data.get('sign_type')}, item_cnt: {data.get('item_cnt')}")

        order_no = get_order_sign_data(control, FID_ORDER_NO)
        item_name = get_order_sign_data(control, FID_ITEM_NAME)
        signed_quantity = get_order_sign_data(control, FID_SETTLEMENT_QTY)
        signed_price = get_order_sign_data(control, FID_SETTLEMENT_PRICE)
        signed_time = get_order_sign_data(control, FID_SETTLEMENT_TIME)
        unsigned_quantity = get_order_sign_data(control, FID_UNDECIDED)
        sign_no = get_order_sign_data(control, FID_SETTLEMENT_NO)

        self.signed_order = SignedOrder(self.order,
                                        order_no=order_no,
                                        item_name=item_name.strip(' '),
                                        undecided_qty=unsigned_quantity,
                                        signed_time=signed_time,
                                        sign_no=sign_no,
                                        sign_price=signed_price,
                                        signed_qty=signed_quantity)

    def get_result(self):
        return {"data": self.signed_order, "error": error_message(self.error_code)}


# class OrderSignHandler:
#     """
#     주식 주문시 체결잔고 데이터 처리
#     """
#     def __init__(self, order):
#         self.order = order
#         self.signed_order = None
#         self.error_message = None
#
#     def handle(self, api, sign_type, item_cnt, fid_list):
#         logger.debug(f"체결잔고 데이터 수신: 체결구분: {sign_type}")
#         self.error_message = None
#
#         order_no = get_order_sign_data(api, FID_ORDER_NO)
#         item_name = get_order_sign_data(api, FID_ITEM_NAME)
#         signed_quantity = get_order_sign_data(api, FID_SETTLEMENT_QTY)
#         signed_price = get_order_sign_data(api, FID_SETTLEMENT_PRICE)
#         signed_time = get_order_sign_data(api, FID_SETTLEMENT_TIME)
#         unsigned_quantity = get_order_sign_data(api, FID_UNDECIDED)
#         sign_no = get_order_sign_data(api, FID_SETTLEMENT_NO)
#
#         self.signed_order = SignedOrder(self.order,
#                                         order_no=order_no,
#                                         item_name=item_name.strip(' '),
#                                         undecided_qty=unsigned_quantity,
#                                         signed_time=signed_time,
#                                         sign_no=sign_no,
#                                         sign_price=signed_price,
#                                         signed_qty=signed_quantity)
#
#     def get_result(self):
#         return {"result": self.signed_order, "error_message": self.error_message}
