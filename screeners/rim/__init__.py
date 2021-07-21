from typing import List
from pandas import DataFrame


class PriceEstimate:

    def __init__(self,
                 stock_code,
                 price_table: DataFrame,
                 applied_roe: float,
                 roe_criteria: str,
                 fiscal_quarter: str,
                 req_profit_rate: float):

        self._table = price_table
        self._stock_code = stock_code
        self._buy_price = int(price_table.iloc[2, 1])
        self._sell_price = int(price_table.iloc[0, 1])
        self._affordable_price = int(price_table.iloc[1, 1])
        self._applied_roe = applied_roe
        self._roe_criteria = roe_criteria
        self._fiscal_quarter = fiscal_quarter
        self._req_profit_rate = req_profit_rate

    def to_dict(self):
        return {'stock_code': self.stock_code,
                'buy_price': self.buy_price,
                'sell_price': self.sell_price,
                'affordable_price': self.affordable_price,
                'roe_estimated': self.applied_roe,
                'roe_criteria': self.roe_criteria,
                'req_profit_rate': self.req_profit_rate,
                'fiscal_quarter': self.fiscal_quarter}

    @property
    def stock_code(self):
        return self._stock_code

    @property
    def applied_roe(self):
        return self._applied_roe

    @applied_roe.setter
    def applied_roe(self, value):
        self._applied_roe = value

    @property
    def roe_criteria(self):
        return self._roe_criteria

    @roe_criteria.setter
    def roe_criteria(self, value):
        self._roe_criteria = value

    @property
    def buy_price(self):
        return self._buy_price

    @property
    def sell_price(self):
        return self._sell_price

    @property
    def affordable_price(self):
        return self._affordable_price

    @property
    def fiscal_quarter(self):
        return self._fiscal_quarter

    @property
    def req_profit_rate(self):
        return self._req_profit_rate

    def as_dataframe(self):
        return self._table


class Criteria:
    ITEMS = ['영업자산이익률', '비영업자산이익률', '차입이자율']
    OPTIONS = ['가중평균', '최근']

    def __init__(self, default_option='가중평균', items: List = None):
        if items is None:
            items = Criteria.ITEMS

        self.items = DataFrame()
        self.items['name'] = items
        self.items.set_index('name', inplace=True)
        self.items['criteria'] = [default_option, default_option, default_option]

    def apply(self, df: DataFrame) -> DataFrame:
        df['criteria'] = self.items['criteria']
        column_selected = 'applied_value'
        df[column_selected] = None

        for i in range(self.items.shape[0]):
            criteria = self.items.iloc[i]['criteria']
            name = self.items.iloc[i].name

            if '가중평균' == criteria:
                df.loc[name, column_selected] = df.loc[name, criteria]
            elif '최근' == criteria:
                filter_col = [col for col in df if col.startswith('최근')]
                df.loc[name, column_selected] = df.loc[name, filter_col[0]]

        return df


