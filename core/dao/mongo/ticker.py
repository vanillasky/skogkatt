from typing import List

from pandas import DataFrame

from skogkatt.core.dao.engine import MongoEngine
from skogkatt.core.dao.idao import TickerDAO
from skogkatt.core.ticker import Ticker


class MongoTickerDAO(TickerDAO):

    def __init__(self, db_name=None, table='ticker'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = table
        self.conn = self._engine.get_connection()

    def find(self,
             stock_code: str = None,
             name: str = None,
             market: str = None,
             corp_code: str = None,
             as_dataframe=False) -> List[Ticker] or DataFrame:
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
        _filter = {}
        if stock_code is not None:
            _filter['code'] = stock_code
        if name is not None:
            _filter['name'] = name
        if market is not None:
            _filter['market'] = market
        if corp_code is not None:
            _filter['corp_code'] = corp_code

        result = list(self._table.find(_filter, {'_id': 0}))

        if as_dataframe:
            return DataFrame(result)

        for record in result:
            ticker_list.append(Ticker.from_dict(record))

        return ticker_list

    def update(self, ticker_df: DataFrame) -> int:
        """
        종목코드 업데이트. DataFrame을 받아서 기존 종목코드 삭제 후 insert.
        Record 단위 삽입, 삭제는 insert 메소드 사용.

        :param ticker_df: DataFrame contains Tickers
        :return: length of the ticker_df
        """
        ticker_list = ticker_df.to_dict(orient='records')
        with self.conn.start_session() as session:
            with session.start_transaction():
                self._table.delete_many({})
                self._table.insert_many(ticker_list)
        return len(ticker_list)

    def insert(self, ticker: Ticker) -> int:
        query = {'code': ticker.code}
        result = self._table.update_one(query, {"$set": ticker.to_dict()}, upsert=True)
        return 1 if result.upserted_id is not None else 0

    def delete(self, stock_code: str = None, name: str = None, market: str = None, corp_code: str = None) -> int:
        """
        :param stock_code:
        :param name:
        :param market:
        :param corp_code:
        :return:
        """
        _filter = {}
        if stock_code is not None:
            _filter['code'] = stock_code
        if name is not None:
            _filter['name'] = name
        if market is not None:
            _filter['market'] = market
        if corp_code is not None:
            _filter['corp_code'] = corp_code

        result = self._table.delete_many(_filter)
        return result.deleted_count

    def count(self, *args, **kwargs) -> int:
        market = kwargs.get('market', None)

        _filter = {}
        if market is not None:
            _filter['market'] = market

        return self._table.count_documents(_filter)

