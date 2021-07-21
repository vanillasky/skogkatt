import sys
import time
from datetime import datetime, timedelta
from queue import Queue

from PyQt5.QtWidgets import QApplication
from pandas import DataFrame

from skogkatt.api.kiwoom.broker import KiwoomBroker
from skogkatt.api.kiwoom.constants import CHART_TR_TIME_INTERVAL
from skogkatt.api.trader import Trader
from skogkatt.batch import batch_lookup
from skogkatt.core.dao import dao_factory
from skogkatt.core.dao.idao import DailyChartDAO
from skogkatt.core.ticker.store import ticker_store
from skogkatt.core.ticker import Ticker
from skogkatt.batch.queue_factory import queue_factory
from skogkatt.errors import PriceRevisedWarning
from skogkatt.commons.util.date import days_between
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


COLUMNS = ['date', 'ticker', 'name', 'open', 'high', 'low', 'close', 'volume']
ROLLING_BASKET = [5, 20, 60, 120]


def append_analysis_columns(stock_code: str, name: str, source_df: DataFrame) -> DataFrame:

    df = DataFrame(source_df, columns=COLUMNS)
    df.sort_values(by='date', ascending=True, inplace=True)
    df['ticker'] = stock_code
    df['name'] = name

    """ 전일대피 등락율 """
    # df['d1_diff_rate'] = round((df['close'] - df['close'].shift(1)) / df['close'].shift(1) * 100, 2)

    """ 이동평균 """
    # for ma in ROLLING_BASKET:
    #     df[f'ma{ma}'] = df['close'].rolling(window=ma).mean()

    df[['open', 'high', 'low', 'close', 'volume']] = \
        df[['open', 'high', 'low', 'close', 'volume']].fillna(0).astype(int)

    return df


class ChartCollector:

    def __init__(self):
        self.broker = KiwoomBroker()
        self.proc_name = batch_lookup.COLLECT_CHART['name']
        self.queue = None
        self.dao: DailyChartDAO = dao_factory.get('DailyChartDAO')

    def start(self, queue=None):
        """
        일봉 챠트 수집 시작. ChartCollector는 서버 호출 횟수 제한을 회피하고자
        일정 시간이 지나면 강제로 프로세스를 종료하고 재시작 하므로
        메소드에 "@batch_status" 데코레이터를 사용하지 않는다.
        "chart_collector_batch.py" 실행시 배치 정보를 DB에 저장하고
        완료시 batch_end 메소드를 호출하여 종료일자를 업데이트 한다.
        :param queue: optional, Queue, 처리할 종목 Ticker
        :return:
        """
        queue = queue if queue is not None else \
            queue_factory.get_queue(self.proc_name, batch_cycle=1, batch_cycle_check=True)

        """ 큐가 비어있는 경우는 배치 실행이 완료되었고, 배치 주기가 도래하지 않았을 때 """
        if queue.empty():
            logger.info('Daily chart date is up to date.')
            if __name__ == '__main__':
                logger.info('Program exit with code 7')
                sys.exit(7)
            else:
                return False

        if self.broker.get_connect_state() < 1:
            self.broker.connect()

        self.collect(queue)

    def collect(self, queue: Queue):
        for count in range(queue.qsize()):
            stock_code = queue.get().get('stock_code')
            ticker = ticker_store.find_by_stock_code(stock_code)

            try:
                # DB에 종목 컬렉션이 없으면 오늘 일자를 기준으로 일봉 데이터 조회해서 저장
                if not self.dao.exists_table(stock_code):
                    chart_df = self.proceed_new_ticker(ticker)
                else:
                    chart_df = self.proceed_exist_ticker(ticker)

                if not chart_df.empty:
                    self.dao.insert(stock_code, chart_df)

                queue_factory.remove_queue_item(self.proc_name, stock_code)

            except PriceRevisedWarning as warn:
                logger.warning(f"수정종가 발생: 종목코드 - {ticker.code}, 종목명 - {ticker.name}")
                self.dao.drop_table(ticker.code)
                queue.put({'batch_name': self.proc_name, 'stock_code': ticker.code})

            time.sleep(CHART_TR_TIME_INTERVAL)

    def proceed_new_ticker(self, ticker: Ticker) -> DataFrame:
        """
        신규 일봉차트 처리. 기준일자부터 데이터를 조회해서 반환한다.
        :param ticker: Ticker, 종목 Ticker
        :return: 일봉 데이터를 담고있는 DataFrame
        """
        from_date = self.resolve_search_date()
        logger.debug(f"Proceed with new ticker: {ticker.code}, search from date {from_date}")

        df = self.broker.get_chart(ticker.code, from_date).get('data')
        if not df.empty:
            df = append_analysis_columns(ticker.code, ticker.name, df)

        return df

    def proceed_exist_ticker(self, ticker: Ticker) -> DataFrame:
        """
        기존 일봉차트 데이터 업데이트 처리
        :param ticker: Ticker, 종목 Ticker
        :return: 일봉 데이터를 담고있는 DataFrame
        :raises: PriceRevisedWarning, 수정종가 발생시
        """
        min_date, max_date = self.dao.min_max_dates(ticker.code)
        logger.debug(
            f"Proceed with existing ticker {ticker}. max_date: {max_date}, min_date: {min_date}")

        recent_chart_df = self.get_recent_chart(ticker, max_date)
        past_chart_df = self.get_past_chart(ticker, min_date)

        if recent_chart_df.empty and past_chart_df.empty:
            return DataFrame()

        df = append_analysis_columns(ticker.code, ticker.name, recent_chart_df.append(past_chart_df))

        return df

    def get_past_chart(self, ticker: Ticker, from_date: str) -> DataFrame:
        """
        과거일자 일봉 업데이트. DB에 저장된 해당 종목의 일봉 데이터 중 가장 오래된 날짜를 기준으로
        증권사 일봉 데이터를 초회해서 DB에 저장한다.
        기준일자로부터 과거 데이터를 조회하므로 결과가 1건이면 과거 데이터는 모두 수집된 것으로 판단.
        :param ticker: Ticker 종목 Ticker
        :param from_date: 조회 기준일자
        :return: 일봉 데이터 DataFrame
        """
        chart_df = self.broker.get_chart(ticker.code, from_date).get('data')
        if len(chart_df) > 1:
            past_chart_df = chart_df[chart_df.date < from_date]
            return past_chart_df
        else:
            logger.debug(f"종목 '{ticker.code}-{ticker.name}'의 일봉 데이터는 증권사에서 제공하는 최초일자({from_date})까지 수집되었음")
            return DataFrame()

    def get_recent_chart(self, ticker: Ticker, from_date: str) -> DataFrame:
        """
        최근 일자 일봉 업데이트. API로부터 오늘(장중이면 어제)일자로 일봉데이터를 받아온다.
        키움증권의 경우 한 번 조회시 600건의 데이터를 넘겨준다. 필요한 개수만 처리하기 위해
        기준일자(오늘 또는 어제)와 DB에 저장된 일봉 데이터의 최근일자간 차이가 나는 날짜 수 만큼만 받아온다.
        :param ticker: 종목코드
        :param name: 종목명
        :param from_date: 조회 기준일자
        :return: 일봉 데이터를 담고있는 DataFrame
        :raises:
            PriceRevisedWarning, 수정종가 발생
        """
        search_date = self.resolve_search_date()    # 장종료 전이면 기준일자를 어제로
        days_diff = days_between(from_date, search_date)

        if days_diff > 0:
            logger.debug(f"days_diff: {days_diff} days, from_date: {from_date}, search_date: {search_date}")
            # API로부터 최근 종가 데이터를 받아온다. 데이터 개수는 DB의 최종일자 이후부터 경과한 날짜 수 만큼만.
            recent_chart_df = self.broker.get_chart(ticker.code, search_date, False, days_diff).get('data')

            if self.is_price_revised(recent_chart_df, ticker.code):
                raise PriceRevisedWarning(stock_code=ticker.code, corp_name=ticker.name)

            recent_chart_df = recent_chart_df[recent_chart_df.date > from_date]
            return recent_chart_df
        else:
            logger.debug(f"종목 '{ticker.code}'의 일봉 데이터는 최근 일자({search_date})까지 수집되었음")
            return DataFrame()

    def is_price_revised(self, chart_df: DataFrame, stock_code: str):
        # API로부터 받아온 데이터중 최초일자 행만 추출
        oldest_chart_df = chart_df[chart_df.date == chart_df.date.min()]

        # DB에서 API 데이터의 최초일자에 해당하는 일봉 데이터 조회
        db_record = self.dao.find_one(stock_code, oldest_chart_df.iloc[0].date)

        if db_record is None:
            return False

        logger.debug(f"Closing price comparison: DB Data {db_record['date']} - {db_record['close']}, "
                     f"API Data {oldest_chart_df.iloc[0].date} - {oldest_chart_df.iloc[0].close}")

        return db_record['close'] != oldest_chart_df.iloc[0].close

    def resolve_search_date(self):
        """
        조회 기준일자를 반환한다.
        장중에 데이터를 수집할 때는 조회 기준일자를 하루 전으로 설정할 수 있도록
        현재시각이 장중인지 확인하여 오늘, 또는 어제 날짜를 반환한다.
        :return: 조회 기준일자
        """
        search_date = None
        now = datetime.now()
        if now < Trader.MARKET_CLOSE:
            yesterday = now - timedelta(1)
            search_date = yesterday.strftime('%Y%m%d')
        else:
            search_date = now.strftime('%Y%m%d')

        return search_date


if __name__ == '__main__':
    app = QApplication(sys.argv)
    collector = ChartCollector()
    collector.start()
