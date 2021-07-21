import re
from datetime import datetime
from pathlib import Path
from typing import List, Union

from pandas import DataFrame

from skogkatt.batch import batch_lookup
from skogkatt.batch.monitor import BatchMonitor
from skogkatt.commons.util.date import days_between
from skogkatt.commons.util.singleton import Singleton
from skogkatt.conf.app_conf import get_project_path
from skogkatt.core import LoggerFactory
from skogkatt.core.dao import dao_factory
from skogkatt.core.ticker import Ticker
from skogkatt.crawler import TickerCrawler
from skogkatt.errors import CrawlerError

logger = LoggerFactory.get_logger(__name__)


def market_type_checker(market: Union[str, list]) -> List[str]:
    """
    Check market types
    :param market: str or List[str]
        market type: S: 유가증권시장, K: 코스닥
    :return:
    """
    if isinstance(market, str):
        market = [x for x in market]

    market = [x.upper() for x in market]

    for m in market:
        if m not in ['S', 'K']:
            raise ValueError('Invalid market type')

    return market


class TickerStore(metaclass=Singleton):

    def __init__(self):
        self._stock_codes = dict()
        self._corp_codes = dict()
        self._corp_names = []

        self.dao = dao_factory.get("TickerDAO")
        self.tickers = self.dao.find()

        if len(self.tickers) == 0:
            logger.info('No ticker data found in database, crawl starts.')
            crawler = TickerCrawler()
            crawler.crawl()
            self.tickers = self.dao.find()
        else:
            monitor = BatchMonitor()
            today = datetime.today()
            status = monitor.get_status(batch_lookup.TICKER['name'])

            if status is None or days_between(status.end, today) > 1:
                logger.info('Ticker data in database is out of date, crawl starts.')
                try:
                    crawler = TickerCrawler()
                    crawler.crawl()
                    self.tickers = self.dao.find()
                except CrawlerError as err:
                    logger.warning(f'Ticker crawling failed. {str(err)}, legacy data will be used.')
            else:
                logger.debug(f'Ticker data in DB is up to date. {status.end}')

        if len(self.tickers) == 0:
            raise ValueError('Cannot resolve ticker data.')

        for idx, x in enumerate(self.tickers):
            self._stock_codes[x.code] = idx
            self._corp_names.append(x.name)
            self._corp_codes[x.corp_code] = idx

    def get_tickers(self) -> List[Ticker]:
        return self.tickers

    def find_by_stock_code(self, code) -> Ticker:
        """
        종목 코드로 검색
        :param code: str
            주식 종목코드
        :return:
            Ticker
        """
        idx = self._stock_codes.get(code)
        return self.tickers[idx] if idx is not None else None

    def find_by_name(self, name, exactly=False) -> List[Ticker]:
        """
        회사명으로 검색
        :param name: str, 회사명
        :param exactly: bool, optional
            name과 정확히 일치  여부(default: False)
        :return:
            List[Ticker]
        """
        ticker_list = []
        if exactly is True:
            name = '^' + name + '$'
        regex = re.compile(name)

        for idx, corp_name in enumerate(self._corp_names):
            if regex.search(corp_name) is not None:
                ticker_list.append(self.tickers[idx])

        return ticker_list

    def find_by_corp_code(self, corp_code):
        """
        회사코드(DART)로 조회
        :param corp_code: str, 회사코드
        :return:
            Ticker
        """
        idx = self._corp_codes.get(corp_code)
        return self.tickers[idx] if idx is not None else None

    def find_by_market(self, market='SK'):
        """
        시장구분으로 조회
        :param market: str or List[str]
            'S': 코스피, 'K': 코스닥
        :return:
        """
        tickers = []
        market = market_type_checker(market)
        for ticker in self.tickers:
            if ticker.market in market:
                tickers.append(ticker)

        return tickers

    def save_file(self, path=None):
        df: DataFrame = self.dao.find(as_dataframe=True)
        if df.empty:
            raise ValueError('Cannot save ticker list. Ticker data is empty.')

        save_path = path if path is not None else get_project_path().joinpath('res')
        if isinstance(save_path, Path):
            save_path = save_path.joinpath('tickers.xlsx')

        df.to_excel(save_path, sheet_name="tickers", index=False)


ticker_store = TickerStore()
