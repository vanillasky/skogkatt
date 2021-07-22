from abc import ABCMeta, abstractmethod
from asyncio import Queue
from typing import List

from pandas import DataFrame

from skogkatt.core.dao.engine import DBEngine
from skogkatt.core.financial import StockSummary


class AbstractDAO(metaclass=ABCMeta):

    def __init__(self):
        self._engine = None
        self._table_name = None

    def get_engine(self) -> DBEngine:
        return self._engine

    def get_table_name(self):
        return self._table_name

    @abstractmethod
    def find(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def update(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def insert(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def delete(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def count(self, *args, **kwargs):
        raise NotImplementedError


class BatchStatusDAO(AbstractDAO):
    from skogkatt.batch import BatchStatus

    @abstractmethod
    def find(self, *args, **kwargs) -> List[BatchStatus] or DataFrame:
        pass

    @abstractmethod
    def update(self, status: BatchStatus) -> int:
        pass

    @abstractmethod
    def insert(self, status: BatchStatus) -> int:
        pass

    @abstractmethod
    def delete(self, name: str = None) -> int:
        pass

    @abstractmethod
    def count(self, batch_name: str = None) -> int:
        pass


class BatchQueueDAO(AbstractDAO):
    @abstractmethod
    def find(self, *args, **kwargs) -> List[Queue]:
        pass


class StockSummaryDAO(AbstractDAO):
    @abstractmethod
    def find(self, stock_codes: List[str] = None) -> List[StockSummary]:
        pass

    @abstractmethod
    def find_one(self, stock_code: str) -> StockSummary or None:
        pass

    @abstractmethod
    def update(self, stock_summary: StockSummary) -> int:
        pass


class TickerDAO(AbstractDAO):
    from skogkatt.core.ticker import Ticker

    @abstractmethod
    def find(self, *args, **kwargs) -> List[Ticker] or DataFrame:
        """
        stock_code: str, 종목코드
        name: str, 종목명
        market: str, 시장구분(S: 코스피, K: 코스닥)
        corp_code: str, 회사코드
        as_dataframe: Bool, DataFrame으로 반환 여부
        :return: List[Ticker] or DataFrame
        """
        pass

    @abstractmethod
    def update(self, ticker_df: DataFrame) -> int:
        """
        :param ticker_df: DataFrame, ticker dataframe
        :return: updated count
        """
        pass

    @abstractmethod
    def insert(self, ticker: Ticker) -> int:
        """
        :param ticker: Ticker object
        :return: inserted count
        """
        pass

    def delete(self, *args, **kwargs) -> int:
        """
        stock_code: str, 종목코드
        name: str, 종목명
        market: str, 시장구분(S: 코스피, K: 코스닥)
        corp_code: str, 회사코드
        :return: int, delete count
        """
        pass


class FnStatementDAO(AbstractDAO):
    def update(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def count(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass


class FnStatementAbbrDAO(AbstractDAO):
    def update(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def count(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass


class RIMPriceEstimateDAO(AbstractDAO):
    def update(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def count(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass


class DailyChartDAO(AbstractDAO):
    def update(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def count(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass

    def find_one(self, *args, **kwargs):
        pass

    def min_max_dates(self, stock_code: str) -> (str, str):
        pass

    def exists_table(self, table_name: str) -> bool:
        pass

    def drop_table(self, table_name: str) -> None:
        pass


class FormulaScreenerDAO(AbstractDAO):
    def update(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def count(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass


class FailedTickerDAO(AbstractDAO):
    def update(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def count(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass
