import time
from datetime import datetime

from tabulate import tabulate
from skogkatt.core import LoggerFactory
from skogkatt.core.dao import dao_factory
from skogkatt.core.ticker.store import ticker_store
from skogkatt.screeners.rim.pricer import Pricer

logger = LoggerFactory.get_logger(__name__)

TR_INTERVAL = 1


class FormulaScreener:

    def __init__(self, broker):
        self.broker = broker
        self.filtered_tickers = {}
        self.crawl = False

    def start(self, crawl=False):
        self.crawl = crawl
        self.broker.connect()
        self.filtered_tickers = self.resolve_formulas()
        self.append_price_estimate()

        dao = dao_factory.get("FormulaScreenerDAO")
        date = datetime.today().strftime("%Y%m%d")
        for key, df in self.filtered_tickers.items():
            dao.update(key, date, df)

        return self.filtered_tickers

    def resolve_formulas(self):
        tickers = {}
        formulas = self.broker.get_filter_formulas()
        for formula in formulas:
            logger.debug(f'조건검색: {formula}')
            df, err_code, message = self.broker.get_filtered_tickers(formula)
            tickers[formula] = df
            time.sleep(TR_INTERVAL)
        return tickers

    def append_price_estimate(self):
        pricer = Pricer()
        for key, df in self.filtered_tickers.items():
            stock_codes = df['stock_code'].values.tolist()

            rim_prices = []

            for stock_code in stock_codes:
                ticker = ticker_store.find_by_stock_code(stock_code)
                estimate = pricer.estimate(ticker, crawl=self.crawl)

                if estimate is None:
                    rim_prices.append([None, None, None, None, None, None])
                else:
                    rim_prices.append([
                        estimate.affordable_price,
                        estimate.buy_price,
                        estimate.sell_price,
                        estimate.roe_criteria,
                        estimate.applied_roe,
                        estimate.req_profit_rate
                    ])

                if self.crawl:
                    time.sleep(TR_INTERVAL)

            date = datetime.today()
            columns = ['affordable', 'buy', 'sell', 'criteria', 'criteria_roe', 'req_profit_rate']
            df[columns] = rim_prices
            df['formula'] = key
            df['date'] = date.strftime("%Y%m%d")


