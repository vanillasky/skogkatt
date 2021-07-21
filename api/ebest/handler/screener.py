from pandas import DataFrame
from tabulate import tabulate

from skogkatt.api import EventHandler, ApiEvent


class FilterFormulaHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self.out_block = "t1857OutBlock"
        self.out_block1 = "t1857OutBlock1"

    def update(self, event: ApiEvent) -> None:
        data = event.data
        xa_query = data.get('query')

        result_count = xa_query.GetFieldData(self.out_block, "result_count", 0).strip()

        count = 0 if len(result_count) == 0 else int(result_count)
        # captured_time = xa_query.GetFieldData(self.out_block, "result_time", 0).strip()
        # alert_key = xa_query.GetFieldData(self.out_block, "AlertNum", 0).strip()

        # print(검색종목수, 포착시간)

        result = []
        for i in range(count):
            stock_code = xa_query.GetFieldData(self.out_block1, "shcode", i).strip()
            name = xa_query.GetFieldData(self.out_block1, "hname", i).strip()
            price = int(xa_query.GetFieldData(self.out_block1, "price", i).strip())
            diff_flag = xa_query.GetFieldData(self.out_block1, "sign", i).strip()
            diff = int(xa_query.GetFieldData(self.out_block1, "change", i).strip())
            diff_rate = float(xa_query.GetFieldData(self.out_block1, "diff", i).strip())
            volume = int(xa_query.GetFieldData(self.out_block1, "volume", i).strip())
            entry_flag = xa_query.GetFieldData(self.out_block1, "JobFlag", i).strip()

            lst = [stock_code, name, price, diff_flag, diff, diff_rate, volume, entry_flag]
            result.append(lst)

        columns = ['stock_code', 'name', 'price', 'diff_flg', 'diff', 'diff_rate', 'volume', 'entry_flag']
        df = DataFrame(data=result, columns=columns)
        self._data = df

