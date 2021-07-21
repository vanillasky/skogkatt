from http.client import RemoteDisconnected
from urllib.error import HTTPError
import xml.etree.ElementTree as elemTree
import pandas as pd
from pandas import DataFrame

from skogkatt.batch import batch_lookup
from skogkatt.conf.crawl_conf import KRX_CORP_LIST_URL
from skogkatt.core.dao import dao_factory
from skogkatt.core.decorators import batch_status
from skogkatt.api.dart import get_corp_code_file
from skogkatt.errors import CrawlerError


class TickerCrawler:

    MARKET_IN_USE = {'S': 'stockMkt', 'K': 'kosdaqMkt'}

    def __init__(self):
        self.ticker_df = None
        self.dao = dao_factory.get("TickerDAO")

    @batch_status(batch_lookup.TICKER['name'])
    def crawl(self, url=None) -> DataFrame:
        """
        한국거래소 주식 종목코드와 금융감독원(DART)의 회사 정보를 읽어 DB에 저장 후 DataFrame을 반환한다.
        DART의 회사코드는 open DART API 이용시 필요함
        :return:
            종목코드 DataFrame
        """

        url = url if url is not None else KRX_CORP_LIST_URL

        try:
            self.ticker_df = self.read_stock_items(url)
            self.append_corp_code()
        except CrawlerError:
            raise

        if self.ticker_df.empty:
            raise CrawlerError(err_msg='Ticker data is empty.')

        self.ticker_df.reset_index(level=0, inplace=True)
        self.dao.update(self.ticker_df)
        return self.ticker_df

    def read_stock_items(self, url):
        """
        거래소 종목코드를 읽어 시장별로 구분하여 Dataframe 을 만든다.
        코스피, 코스닥 종목만 처리한다.
        :return: Dataframe, 종목코드, 종목명 등
        """
        ticker_df = pd.DataFrame()
        try:
            for market, market_type in TickerCrawler.MARKET_IN_USE.items():
                search_url = f'{url}&searchType=13&marketType={market_type}'
                company_df = pd.read_html(search_url, header=0)[0]
                company_df = self.trim(company_df)
                company_df['market'] = market

                ticker_df = ticker_df.append(company_df)

            ticker_df = ticker_df.set_index('code')
            return ticker_df

        except (HTTPError, RemoteDisconnected) as err:
            raise CrawlerError(err)

    @staticmethod
    def trim(df):
        """
        종목코드에서 필요한 컬럼만 추출한다.
        :param df: 원본 종목코드 DataFrame
        :return: 종목코드, 회사명, 결산원, 상장일, 업종을 담고 있는 DataFrame
        """

        # 한글로된 컬럼명을 영어로 바꿔준다.
        stock_items = df.rename(columns={'종목코드': 'code', '회사명': 'name',
                                         '결산월': 'acc_date', '상장일': 'ipo_date',
                                         '업종': 'industry'})

        # 6자리 만들고 앞에 0을 붙인다
        stock_items['code'] = stock_items['code'].map('{:06d}'.format)
        stock_items['name'] = stock_items['name'].str.strip()

        # 종목코드, 종목명, 결산월, 상장일, 업종 추출
        ticker_df = stock_items[['code', 'name', 'acc_date', 'ipo_date', 'industry']]
        ticker_df = ticker_df.sort_values(by='code')
        return ticker_df

    def append_corp_code(self):
        """
        종목정보 Dataframe 에 open DART 회사 코드 추가
        :return:
        """
        file = get_corp_code_file()
        doc = elemTree.parse(file)
        root = doc.getroot()

        for node in root.findall('list'):
            stock_code = node.find('stock_code').text.strip()
            corp_code = node.find('corp_code').text

            if len(stock_code) > 0 and stock_code in self.ticker_df.index:
                self.ticker_df.loc[stock_code, 'corp_code'] = corp_code

