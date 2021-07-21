from typing import List

import pymongo
from pandas import DataFrame

from skogkatt.core import LoggerFactory
from skogkatt.core.dao.engine import MongoEngine
from skogkatt.core.dao.idao import DailyChartDAO

logger = LoggerFactory.get_logger(__name__)


class MongoDailyChartDAO(DailyChartDAO):

    def __init__(self, db_name=None, table=None):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = None
        self._table_name = table
        self.db = self._engine.get_db()
        # self._table = self._engine.get_db()[table]
        # self._table_name = table
        self.conn = self._engine.get_connection()

    def min_max_dates(self, stock_code) -> (str, str):
        """
        해당 종목의 일봉 자료 중 최초, 최종일자를 반환한다.
        :param stock_code: str, 종목코드
        :return:
            최초일자, 최종일자
        """
        result = self.db[stock_code].aggregate([
                            {"$group": {
                                "_id": 'min_max',
                                "max": {"$max": "$date"},
                                "min": {"$min": "$date"}
                            }}
                        ])

        date_list = list(result)
        return date_list[0]['min'], date_list[0]['max']

    def find_one(self, stock_code: str, date: str):
        if self.exists_table(stock_code):
            return self.db[stock_code].find_one({"date": date})

        return None

    def find(self, stock_code: str, from_date: str = None, to_date: str = None) -> List[dict]:
        if not self.exists_table(stock_code):
            return []

        where = [{'ticker': stock_code}]
        if from_date is not None:
            where.append({'date': {"$gte": from_date}})

        if to_date is not None:
            where.append({'date': {"$lte": to_date}})

        query = {'$and': where}
        records = list(self.db[stock_code].find(query, {'_id': 0}).sort([("date", pymongo.ASCENDING)]))
        return records

    def insert(self, stock_code: str, df: DataFrame):
        if df is None or df.empty:
            logger.warning('Dataframe is None or empty, could not insert.')
            return

        self.db[stock_code].insert_many(df.to_dict(orient="records"))

    def exists_table(self, stock_code: str):
        return self._engine.exists_table(stock_code)

    def drop_table(self, stock_code: str):
        return self.db.drop_collection(stock_code)

