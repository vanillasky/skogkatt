from collections import defaultdict

from pandas import DataFrame
from tabulate import tabulate

from skogkatt.api import EventHandler, ApiEvent


class DailyChartHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self.out_block = "t1305OutBlock"
        self.out_block1 = "t1305OutBlock1"
        self.chart = defaultdict(list)

    def update(self, event: ApiEvent) -> None:
        self._error_code = event.error_code
        self._message = event.message

        xa_query = event.data.get('query')

        if xa_query is None:
            return

        next_date = xa_query.GetFieldData(self.out_block, "date", 0).strip()
        # row_cnt = int(xa_query.GetFieldData(self.out_block, "cnt", 0).strip())
        # idx = int(xa_query.GetFieldData(self.out_block, "idx", 0).strip())

        result = []
        row_cnt = xa_query.GetBlockCount(self.out_block1)
        for i in range(row_cnt):
            date = xa_query.GetFieldData(self.out_block1, "date", i).strip()
            open_price = int(xa_query.GetFieldData(self.out_block1, "open", i).strip())
            high_price = int(xa_query.GetFieldData(self.out_block1, "high", i).strip())
            low_price = int(xa_query.GetFieldData(self.out_block1, "low", i).strip())
            close_price = int(xa_query.GetFieldData(self.out_block1, "close", i).strip())
            volume = int(xa_query.GetFieldData(self.out_block1, "volume", i).strip())

            self.chart['date'].append(date)
            self.chart['open'].append(int(open_price))
            self.chart['high'].append(int(high_price))
            self.chart['low'].append(int(low_price))
            self.chart['close'].append(int(close_price))
            self.chart['volume'].append(int(volume))

            # 전일대비구분 = xa_query.GetFieldData(self.out_block1, "sign", i).strip()
            # 전일대비 = int(xa_query.GetFieldData(self.out_block1, "change", i).strip())
            # 등락율 = float(xa_query.GetFieldData(self.out_block1, "diff", i).strip())
            # 거래증가율 = float(xa_query.GetFieldData(self.out_block1, "diff_vol", i).strip())
            # 체결강도 = float(xa_query.GetFieldData(self.out_block1, "chdegree", i).strip())
            # 소진율 = float(xa_query.GetFieldData(self.out_block1, "sojinrate", i).strip())
            # 회전율 = float(xa_query.GetFieldData(self.out_block1, "changerate", i).strip())
            # 외인순매수 = int(xa_query.GetFieldData(self.out_block1, "fpvolume", i).strip())
            # 기관순매수 = int(xa_query.GetFieldData(self.out_block1, "covolume", i).strip())
            # 종목코드 = xa_query.GetFieldData(self.out_block1, "shcode", i).strip()
            # 누적거래대금 = int(xa_query.GetFieldData(self.out_block1, "value", i).strip())
            # 개인순매수 = int(xa_query.GetFieldData(self.out_block1, "ppvolume", i).strip())
            # 시가대비구분 = xa_query.GetFieldData(self.out_block1, "o_sign", i).strip()
            # 시가대비 = int(xa_query.GetFieldData(self.out_block1, "o_change", i).strip())
            # 시가기준등락율 = float(xa_query.GetFieldData(self.out_block1, "o_diff", i).strip())
            # 고가대비구분 = xa_query.GetFieldData(self.out_block1, "h_sign", i).strip()
            # 고가대비 = int(xa_query.GetFieldData(self.out_block1, "h_change", i).strip())
            # 고가기준등락율 = float(xa_query.GetFieldData(self.out_block1, "h_diff", i).strip())
            # 저가대비구분 = xa_query.GetFieldData(self.out_block1, "l_sign", i).strip()
            # 저가대비 = int(xa_query.GetFieldData(self.out_block1, "l_change", i).strip())
            # 저가기준등락율 = float(xa_query.GetFieldData(self.out_block1, "l_diff", i).strip())
            # 시가총액 = int(xa_query.GetFieldData(self.out_block1, "marketcap", i).strip())

        self._data = self.chart

    def get_result(self):
        return self.as_dataframe(), self.error_code, self.message

    def as_dataframe(self) -> DataFrame:
        if len(self.chart) > 0:
            df = DataFrame(self.chart, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            return df

        return DataFrame()
