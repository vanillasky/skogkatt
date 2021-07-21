from collections import defaultdict

from pandas import DataFrame

from skogkatt.api import EventHandler
from skogkatt.api.kiwoom import error_message
from skogkatt.api.kiwoom.event import ApiEvent
from skogkatt.api.kiwoom.rmi import get_repeat_cnt, get_comm_data
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class DailyChartHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self.chart = defaultdict(list)

    def update(self, event: ApiEvent) -> None:
        if event.error_code < 0:
            raise RuntimeError(error_message(event.error_code))

        api = event.data.get("control")
        tr_code = event.data.get("tr_code")
        rq_name = event.data.get("rq_name")

        data_cnt = get_repeat_cnt(api, tr_code, rq_name)

        if self.limit is not None and self.limit > 0:
            logger.debug(f"Actual loop count from API was {data_cnt}, reset the loop count to {self.limit}.")
            if data_cnt < self.limit:
                data_cnt = data_cnt
            else:
                data_cnt = self.limit

        for i in range(data_cnt):
            date = get_comm_data(api, tr_code, rq_name, i, "일자").strip()
            open_price = get_comm_data(api, tr_code, rq_name, i, "시가")
            high_price = get_comm_data(api, tr_code, rq_name, i, "고가")
            low_price = get_comm_data(api, tr_code, rq_name, i, "저가")
            close_price = get_comm_data(api, tr_code, rq_name, i, "현재가")
            volume = get_comm_data(api, tr_code, rq_name, i, "거래량")

            # date = datetime.strptime(date, '%Y%m%d')
            self.chart['date'].append(date)
            self.chart['open'].append(int(open_price))
            self.chart['high'].append(int(high_price))
            self.chart['low'].append(int(low_price))
            self.chart['close'].append(int(close_price))
            self.chart['volume'].append(int(volume))

    def get_result(self):
        return {'data': self.as_dataframe(), 'error': None}

    def as_dataframe(self) -> DataFrame:
        if len(self.chart) > 0:
            df = DataFrame(self.chart, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            return df

        return DataFrame()


# class DailyChartHandler:
#     """
#     주식 일봉 자료 처리
#     """
#
#     def __init__(self):
#         self.chart = defaultdict(list)
#         self.limit = None
#
#     def set_limit(self, limit):
#         self.limit = limit
#
#     def handle(self, api, screen_no, rq_name, tr_code, record_name, _next):
#         data_cnt = get_repeat_cnt(api, tr_code, rq_name)
#
#         if self.limit is not None and self.limit > 0:
#             logger.debug(f"Actual loop count from API was {data_cnt}, reset the loop count to {self.limit}.")
#             if data_cnt < self.limit:
#                 data_cnt = data_cnt
#             else:
#                 data_cnt = self.limit
#
#         for i in range(data_cnt):
#             date = get_comm_data(api, tr_code, rq_name, i, "일자").strip()
#             open_price = get_comm_data(api, tr_code, rq_name, i, "시가")
#             high_price = get_comm_data(api, tr_code, rq_name, i, "고가")
#             low_price = get_comm_data(api, tr_code, rq_name, i, "저가")
#             close_price = get_comm_data(api, tr_code, rq_name, i, "현재가")
#             volume = get_comm_data(api, tr_code, rq_name, i, "거래량")
#
#             # date = datetime.strptime(date, '%Y%m%d')
#             self.chart['date'].append(date)
#             self.chart['open'].append(int(open_price))
#             self.chart['high'].append(int(high_price))
#             self.chart['low'].append(int(low_price))
#             self.chart['close'].append(int(close_price))
#             self.chart['volume'].append(int(volume))
#
#     def get_result(self):
#         return {'result': self.chart, 'err_message': None}
#
#     def as_dataframe(self) -> DataFrame:
#         if len(self.chart) > 0:
#             df = DataFrame(self.chart, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
#             return df
#
#         return DataFrame()
