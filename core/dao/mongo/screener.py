from typing import List

from pandas import DataFrame

from skogkatt.core.dao.engine import MongoEngine
from skogkatt.core.dao.idao import FormulaScreenerDAO
from skogkatt.core.ticker import Ticker


class MongoFormulaScreenerDAO(FormulaScreenerDAO):

    def __init__(self, db_name=None, table='screen_report'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = table
        self.conn = self._engine.get_connection()

    def find(self,
             screener_name: str = None,
             from_date: str = None,
             to_date: str = None,
             as_dataframe=False) -> DataFrame:
        """
        :param screener_name: str, 조건검색명
        :param from_date: str, 년월일
        :param to_date: str, 년월일
        :param as_dataframe: Bool, DataFrame으로 반환 여부
        :return:
            DataFrame
        """

        where = []

        if screener_name is not None:
            where.append({'formula': screener_name})

        if from_date is not None:
            where.append({'date': {"$gte": from_date}})

        if to_date is not None:
            where.append({'date': {"$lte": to_date}})

        query = {'$and': where} if len(where) > 0 else {}
        result = list(self._table.find(query, {'_id': 0}))

        return DataFrame(result)

    def update(self, screener_name: str, date: str, stock_df: DataFrame) -> int:
        """
        종목코드 업데이트. DataFrame을 받아서 기존 종목코드 삭제 후 insert.
        Record 단위 삽입, 삭제는 insert 메소드 사용.
        :param screener_name: str, 조건검색명
        :param date: str, 년월일
        :param stock_df: DataFrame contains Tickers
        :return: length of the ticker_df
        """
        ticker_list = stock_df.to_dict(orient='records')
        query = {'formula': screener_name, 'date': date}
        print(query)
        with self.conn.start_session() as session:
            with session.start_transaction():
                self._table.delete_many(query)
                self._table.insert_many(ticker_list)
        return len(ticker_list)

    def insert(self, ticker: Ticker) -> int:
        query = {'code': ticker.code}
        result = self._table.update_one(query, {"$set": ticker.to_dict()}, upsert=True)
        return 1 if result.upserted_id is not None else 0