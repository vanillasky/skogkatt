from typing import List

from pandas import DataFrame

from skogkatt.core import LoggerFactory
from skogkatt.core.dao.engine import MariaEngine
from skogkatt.core.dao.idao import TickerDAO
from skogkatt.core.dao.maria import make_query
from skogkatt.core.ticker import Ticker

logger = LoggerFactory.get_logger(__name__)


class MariaTickerDAO(TickerDAO):

    def __init__(self, db_name=None, table='ticker'):
        super().__init__()
        self._engine = MariaEngine(db_name)
        self._table_name = table
        self.conn = self._engine.get_connection()

    def find(self,
             stock_code: str = None,
             name: str = None,
             market: str = None,
             corp_code: str = None,
             as_dataframe=False) -> List[Ticker] or None:
        """
        :param stock_code: str, 종목코드
        :param name: str, 종목명
        :param market: str, 시장구분(S: 코스피, K: 코스닥)
        :param corp_code: str, 회사코드
        :param as_dataframe: Bool, DataFrame으로 반환 여부
        :return:
            List[Ticker] or DataFrame
        """
        ticker_list = []

        sql = f"select * from {self._table_name} where 1=1"
        conditions, params = make_query('eq', code=stock_code, name=name, market=market, corp_code=corp_code)

        sql = sql + ''.join(conditions)
        result = self.conn.execute(sql, params).fetchall()

        if as_dataframe:
            return DataFrame(result, columns=['code', 'name', 'acc_date', 'ipo_date', 'industry', 'market', 'corp_code'])

        for record in result:
            ticker_list.append(Ticker.from_dict(record))

        return ticker_list

    def update(self, ticker_df: DataFrame) -> int:
        ticker_df.to_sql(name=f'{self._table_name}', con=self.conn, if_exists='replace', index=False)
        return ticker_df.shape[0]

    def insert(self, ticker: Ticker) -> int:
        sql = f"insert into {self._table_name} (code, name, acc_date, ipo_date, industry, market, corp_code) " \
              f"values (%s, %s, %s, %s, %s, %s, %s) " \
              f"on duplicate key update " \
              f"name = %s, acc_date = %s, ipo_date = %s, industry = %s, market = %s, corp_code = %s"

        params = (ticker.code, ticker.name, ticker.acc_date, ticker.ipo_date, ticker.industry, ticker.market, ticker.corp_code,
                  ticker.name, ticker.acc_date, ticker.ipo_date, ticker.industry, ticker.market, ticker.corp_code)

        result = self.conn.execute(sql, params)
        return result.rowcount

    def delete(self, stock_code: str = None, name: str = None, market: str = None, corp_code: str = None) -> int:
        sql = f"delete from {self._table_name} where 1=1"
        conditions, params = make_query('eq', code=stock_code, name=name, market=market, corp_code=corp_code)

        sql = sql + ' '.join(conditions)
        result = self.conn.execute(sql, params)
        return result.rowcount

    def count(self, *args, **kwargs) -> int:
        # market = kwargs.get('market', None)
        sql = f"select count(code) as cnt from {self._table_name} where 1=1"

        conditions, params = make_query('eq', **kwargs)

        sql = sql + ''.join(conditions)
        result = self.conn.execute(sql, params).fetchall()
        return result[0][0]
