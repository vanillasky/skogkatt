from typing import List

import pymongo
from pandas import DataFrame
from pymongo.collection import Collection

from skogkatt.core.dao.engine import MongoEngine
from skogkatt.core.financial import Statement
from skogkatt.core.financial import StockSummary
from skogkatt.core.dao.idao import StockSummaryDAO, FnStatementDAO
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class MongoStockSummaryDAO(StockSummaryDAO):
    def __init__(self, db_name='skogkatt_fn_statement', table='stock_summary'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = table
        self.conn = self._engine.get_connection()

    def update(self, stock_summary: StockSummary) -> int:
        query = {'stock_code': stock_summary.stock_code}
        result = self._table.update_one(query, {"$set": stock_summary.to_dict()}, upsert=True)
        return 1 if result.upserted_id is not None else 0

    def find(self, stock_codes: List[str] = None) -> List[StockSummary]:
        query = {'stock_code': {'$in': stock_codes}} if stock_codes is not None else {}
        records = list(self._table.find(query))
        summary_list = []
        for each in records:
            summary_list.append(StockSummary.from_dict(each))

        return summary_list

    def find_one(self, stock_code: str) -> StockSummary or None:
        result = self._table.find_one({'stock_code': stock_code})
        if result is None:
            return None

        return StockSummary.from_dict(result)

    def insert(self, stock_summary: StockSummary) -> int:
        return self.update(stock_summary)

    def delete(self, stock_code: str = None) -> int:
        _filter = {}
        if stock_code is not None:
            _filter['stock_code'] = stock_code

        result = self._table.delete_many(_filter)
        return result.deleted_count

    def count(self, *args, **kwargs):
        return self._table.count_documents({})


class MongoFnStatementDAO(FnStatementDAO):
    def __init__(self, db_name='skogkatt_fn_statement', table='statement'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = table
        self.conn = self._engine.get_connection()

    def update(self, statements: List[Statement]) -> int:
        """
        재무제표 자료를 삽입한다.
        년, 월, 연간/분기, 연결/개별 구분을 기준으로 해당 자료가 있으면 삭제하고 삽입.
        :param statements: List of Statements, 재무제포
        :return:
            insert 자료 수
        """
        with self.conn.start_session() as session:
            with session.start_transaction():
                inserted_cnt = 0
                for stmt in statements:
                    query = {'stock_code': stmt.stock_code,
                             'fiscal_date': stmt.fiscal_date,
                             'report_code': stmt.report_code,
                             'fs_div': stmt.fs_div}

                    legacy_cnt = self._table.count_documents(query)
                    if legacy_cnt > 0:
                        self._table.delete_many(query)

                    result = self._table.insert_many(stmt.to_dataframe().to_dict(orient='records'))
                    inserted_cnt += len(result.inserted_ids)

                return inserted_cnt

    # def get_raw_statements(self, query: dict = None) -> List[dict]:
    #     """
    #     재무제표 Raw Data 반환
    #     :param stock_code: str, 종목코드
    #     :param query: dict, 검색조건
    #     :return:
    #         dict list
    #     """
    #     return list(self._table.find(query))
    #
    # def get_raw_abbreviation(self, query: dict = None) -> List[dict]:
    #     return list(self.col_abbr.find(query))
    def _find_statement(self,
                        stock_code: str,
                        report_code: int,
                        from_date: str = None,
                        to_date: str = None,
                        consensus: int = 0) -> List[dict]:

        where = [{'stock_code': stock_code}, {'report_code': report_code}]
        if consensus is not None:
            where.append({'consensus': consensus})

        if from_date is not None:
            where.append({'fiscal_date': {"$gte": from_date}})

        if to_date is not None:
            where.append({'fiscal_date': {"$lte": to_date}})

        query = {'$and': where}
        logger.debug(f'cond: {query}')
        records = list(self._table.find(query, {'_id': 0}).sort([("fiscal_date", pymongo.ASCENDING)]))

        return records

    def find(self,
             stock_code: str,
             report_code: int,
             from_date: str = None,
             to_date: str = None,
             consensus: int = 0) -> List[Statement]:

        records = self._find_statement(stock_code, report_code, from_date, to_date, consensus)

        statement_list = []
        if len(records) == 0:
            return statement_list

        df = DataFrame(records)
        # print(tabulate(df, headers="keys", tablefmt="psql"))
        grouped = df.groupby(['stock_code', 'fiscal_date', 'consensus', 'fs_div'])

        for group_columns, group in grouped:
            statement = Statement.create(stock_code=group_columns[0],
                                         fiscal_date=group_columns[1],
                                         consensus=group_columns[2],
                                         fs_div=group_columns[3],
                                         report_code=report_code)

            sectored = group.groupby(['sector', 'attribute', 'sj_div'])
            for group_name, sector in sectored:
                accounts = sector['account_id'].values.tolist()
                values = sector['value'].values.tolist()
                statement.append_facts(accounts=accounts,
                                       values=values,
                                       sector=group_name[0],
                                       group=group_name[1],
                                       sj_div=group_name[2])

            statement_list.append(statement)

        return statement_list

    def delete(self, stock_code: str = None, fiscal_date: str = None):
        _filter = {}
        if stock_code is not None:
            _filter['stock_code'] = stock_code
        if fiscal_date is not None:
            _filter['fiscal_date'] = fiscal_date

        result = self._table.delete_many(_filter)
        return result.deleted_count

    def count(self,
              stock_code: str = None,
              report_code: int = None,
              from_date: str = None,
              to_date: str = None,
              consensus: int = 0) -> int:

        where = []
        if stock_code is not None:
            where.append({'stock_code': stock_code})
        if report_code is not None:
            where.append({'report_code': report_code})
        if consensus is not None:
            where.append({'consensus': consensus})
        if from_date is not None:
            where.append({'fiscal_date': {"$gte": from_date}})
        if to_date is not None:
            where.append({'fiscal_date': {"$lte": to_date}})

        query = {'$and': where}
        # logger.debug(f'cond: {query}')

        return self._table.count_documents(query)


class MongoFnStatementAbbrDAO(MongoFnStatementDAO):
    def __init__(self, db_name='skogkatt_fn_statement', table='abbreviation'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = table
        self.conn = self._engine.get_connection()

    def find(self,
             stock_code: str,
             report_code: int,
             from_date: str = None,
             to_date: str = None,
             consensus: int = 0) -> List[Statement]:

        records = self._find_statement(stock_code, report_code, from_date, to_date, consensus)

        statement_list = []
        if len(records) == 0:
            return statement_list

        df = DataFrame(records)
        # print(tabulate(df, headers="keys", tablefmt="psql"))
        grouped = df.groupby(['stock_code', 'fiscal_date', 'consensus', 'fs_div'])

        """ FnGuide Snapshot 자료는 섹터별로 나누지 않으므로 별도로 처리한다."""
        for group_columns, group in grouped:
            statement = Statement.create(stock_code=group_columns[0],
                                         fiscal_date=group_columns[1],
                                         consensus=group_columns[2],
                                         fs_div=group_columns[3],
                                         report_code=report_code)

            accounts = group['account_id'].values.tolist()
            values = group['value'].values.tolist()
            statement.append_facts(accounts=accounts, values=values, sector=None, group=None, sj_div=None)

            statement_list.append(statement)

        return statement_list

# class UnresolvedTickerDao(BaseDao):
#
#     def __init__(self):
#         super().__init__()
#         self.collection = self.db['unresolved_ticker']
#
#     def update(self, tickers: List[dict], proc_name: str):
#         with self.engine.start_session() as session:
#             with session.start_transaction():
#                 self.collection.delete_many({'proc': proc_name})
#                 self.collection.insert_many(tickers)
#
#     def find(self, as_dataframe: bool = False):
#         records = list(self.collection.find({}, {'_id': 0}))
#         if as_dataframe:
#             return DataFrame(records)
#
#         return records

