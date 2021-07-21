import logging
import math
import calendar
from datetime import datetime
from typing import List, Tuple

import numpy
import pandas as pd
from pandas import DataFrame
from tabulate import tabulate

from skogkatt.commons.util.date import get_fiscal_date, days_between
from skogkatt.commons.util.numeral import format_with
from skogkatt.core import LoggerFactory
from skogkatt.core.dao import dao_factory
from skogkatt.core.dao.idao import StockSummaryDAO, FnStatementAbbrDAO
from skogkatt.core.financial import Statement
from skogkatt.core.financial.dto import FinancialStatementDTO
from skogkatt.core.ticker import Ticker
from skogkatt.crawler.fnguide.parser import FnSnapshotParser, FnStatementParser
from skogkatt.crawler.fnguide.scraper import FnGuideSnapshotScraper, FnGuideStatementScraper
from skogkatt.errors import PricerError, NoDataFoundError, StatementParseError
from skogkatt.screeners.rim import PriceEstimate
from skogkatt.screeners.rim.estimator import ROEEstimator

from skogkatt.screeners.rim.helper import DBHelper

logger = LoggerFactory.get_logger(__name__)

# S-RIM 분석 년수
ANALYSIS_YEARS = 10

# 초과이익 계수
COEFFICIENTS = [{'label': '초과이익 지속', 'coefficient': 1.0, 'decision': '매도가격'},
                {'label': '10%씩 감소', 'coefficient': 0.9, 'decision': '적정가격'},
                {'label': '20%씩 감소', 'coefficient': 0.8, 'decision': '매수가격'}]

# 요구 수익율
REQ_PROFIT_RATE = 7.89


def pivot_table(df_source: DataFrame):
    """
    년/월별 행으로 구성된 테이블을 년/월 컬럼 형태로 변환해서 반환한다.
    :param df_source:
    :return:
        DataFrame looks like:
        +---------+------------------+------------------+------------------+-----------------+------------------+
        |         |           2020/3 |           2020/6 |           2020/9 |         2020/12 |           2021/3 |
        |---------+------------------+------------------+------------------+-----------------+------------------|
        | 매출액     | 553252           | 529661           | 669642           | 615515          | 653885          |
        | 지배주주순이익 |  48896           |  54890           |  92668           |  64455          |  70928       |
        | 지배주주지분  |      2.58482e+06 |      2.61745e+06 |      2.67942e+06 |      2.6767e+06 |   2.65767e+06 |
        | ROE     |      7.62        |      8.44        |     14           |      9.63       |     10.64        |
        +---------+------------------+------------------+------------------+-----------------+------------------+
    """
    df = DataFrame()

    groups = df_source.groupby(['fiscal_date'])
    group_data = None
    for date, group_data in groups:
        df[date] = group_data['value']

    df.index = group_data['account_id'].values.tolist()
    return df


def extract_facts(statements: List[Statement], accounts: Tuple = None, consensus: int = 0) -> DataFrame:
    """
    재무제표에서 필요한 항목만 추출해서 반환한다.
    :param accounts: Tuple, 추출할 계정과목 리스트
    :param statements: List[Statement], 재무제표 리스트
    :param consensus: int, 컨센서스 포함여부 1: 컨센서스, 0: 실적자료, 2: 컨센 + 실적
    :return:
        DataFrame
    """
    df = DataFrame()
    for stmt in statements:
        df_stmt = stmt.to_dataframe()

        if consensus != 2:
            df_stmt = df_stmt[df_stmt['consensus'] == consensus]

        if accounts is not None:
            df_stmt = df_stmt.loc[df_stmt['account_id'].isin(accounts)]

        df = df.append(df_stmt)

    df = df.drop(['attribute', 'sector', 'sj_div'], axis=1)
    return df


def get_annual_fact(statements: List[Statement]) -> DataFrame:
    df = extract_facts(statements, ('지배주주지분', '지배주주순이익', 'ROE'), consensus=2)
    df = df.sort_values(by=['fiscal_date'])
    df = pivot_table(df)

    return df


def get_quarter_fact(statements: List[Statement]) -> DataFrame:
    df = extract_facts(statements, ('매출액', '지배주주지분', '지배주주순이익', 'ROE'))
    df = df.sort_values(by=['fiscal_date'])
    df = pivot_table(df)
    return df


def calc_quarter_roe(ticker: Ticker, df_quarters: DataFrame) -> DataFrame:
    """
    분기자료로 최근 4분기 ROE를 계산해서 반환한다.
    :return:
        DataFrame looks like:
        +---------+------------------+
        |         |           2021/3 |
        |---------+------------------|
        | 지배주주순이익 | 282941           |
        | 지배주주지분  |      2.65767e+06 |
        | ROE     |     10.79        |
        +---------+------------------+
    """
    print(tabulate(df_quarters, headers="keys", tablefmt="psql"))
    # 매출액 Min value
    min_sales = df_quarters.loc['매출액'].min()

    # 지배주주지분 Min value
    min_ctrl_interest = df_quarters.loc["지배주주지분"].min()

    # 매출액, 지배주주지분 값이 없으면 분기자료 부족으로 처리
    if min(min_sales, min_ctrl_interest) <= 0:
        raise PricerError('최근분기 ROE 계산 실패 - 분기자료 부족: 매출액, 지배주주지분: ',
                          stock_code=ticker.code, corp_name=ticker.name, industry=ticker.industry)

    # 지배주주지분(최근분기)
    ctrl_interest = df_quarters.loc['지배주주지분', df_quarters.columns[-1]]

    # 지배주주지분 평균(첫번째, 최근 분기만)
    ctrl_interest_avg = df_quarters.loc['지배주주지분', df_quarters.columns[[0, -1]]].mean()

    # 지배주주 순이익(최근 4분기 합계)
    sum_ctrl_income = df_quarters.loc['지배주주순이익', df_quarters.columns[1:]].sum()

    # 지배주주 ROE = 지배주주 순이익 / 지배주주지분
    roe = round(sum_ctrl_income / ctrl_interest_avg * 100, 2)

    logger.debug(f'분기자료 ROE 분석결과 - 매출액:{min_sales}, '
                 f'지배주주지분:{min_ctrl_interest}, 지배주주지분평균:{ctrl_interest_avg},'
                 f'지배주주순이익:{sum_ctrl_income}, ROE: {roe}')

    result_df = DataFrame(columns=[f'{df_quarters.columns[-1]}'], index=['지배주주순이익', '지배주주지분', 'ROE'])
    result_df.loc['지배주주순이익', result_df.columns[0]] = sum_ctrl_income
    result_df.loc['지배주주지분', result_df.columns[0]] = ctrl_interest
    result_df.loc['ROE', result_df.columns[0]] = roe

    return result_df


class Pricer:

    def __init__(self):
        self.price_estimate: PriceEstimate = None
        self.db_helper = DBHelper()

        self.quarter_fiscal_year, self.quarter_fiscal_month = get_fiscal_date()

        self.dto: FinancialStatementDTO = None
        self.fact_table: DataFrame = None
        self.ticker: Ticker = None

        self.req_profit_rate = None     # 요구수익률
        self.std_date = None            # 분석기준 일자
        self.days_elapsed = None        # 기준시점 - 현재
        self.equity_on_std_date = None  # 기준시점 주주지분

    def estimate(self, ticker: Ticker, req_profit_rate: float = REQ_PROFIT_RATE, crawl=False) -> PriceEstimate or None:
        """
        ROE, 요구수익률을 적용한 RIM 적정가격을 계산해서 반환한다.
        :param ticker: Ticker, 종목 티커
        :param req_profit_rate: float, 요구 수익률 %
        :param crawl, Bool, 재무정보가 DB에 없을 경우 크롤링 여부
        :return:
            DataFrame looks like:
            ---------------------------------------------------
                       적정주주가치      적정주가    PER    판단
            ---------------------------------------------------
            초과이익지속   3909907       57560    18.18    매도가격
            10%씩 감소    3510497       51680    16.32    적정가격
            20%씩 감소    3264351       48056    15.18    매수가격
        """

        logger.info(f"S-RIM Pricer starts: {ticker.name}({ticker.code}), "
                    f"recent fiscal quarter: {self.quarter_fiscal_year}/{self.quarter_fiscal_month},"
                    f"required profit rate: {req_profit_rate}")

        self.ticker = ticker
        self.req_profit_rate = req_profit_rate

        try:
            self.dto = self.db_helper.get_fn_statement_dto(ticker.code)
        except NoDataFoundError as err:
            if not crawl:
                logger.info(f"Financial data not found in DB, return None")
                return None

            logger.info(f"Financial data not found in DB, trying to crawl and store: {ticker.code}")
            self.dto = self._prepare_fn_statement(ticker.code)

        try:
            annual_fact_df = get_annual_fact(self.dto.annual_abbreviations)
            quarter_fact_df = get_quarter_fact(self.dto.quarter_abbreviations)
            quarter_roe_df = calc_quarter_roe(self.ticker, quarter_fact_df)

            applied_roe, roe_criteria = self._resolve_roe(quarter_roe_df)

            self.fact_table = pd.concat([annual_fact_df, quarter_roe_df], axis=1)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'S-RIM fact table: {ticker.name}({ticker.code})')
                logger.debug(tabulate(self.fact_table, headers="keys", tablefmt="psql", numalign="right"))

            self.resolve_time_factor(applied_roe)
            baseline = self.create_baseline(applied_roe)

            df_result = self._estimate_prices(baseline)
        except PricerError as err:
            logger.error(str(err))
            return None

        price_estimate = PriceEstimate(ticker.code,
                                       df_result,
                                       applied_roe,
                                       roe_criteria,
                                       quarter_roe_df.columns[0],
                                       req_profit_rate)

        return price_estimate

        # print(tabulate(df_result, headers="keys", tablefmt="psql", numalign="right"))

    def _prepare_fn_statement(self, stock_code):
        snapshot_file = FnGuideSnapshotScraper.scrape(stock_code)
        statement_file = FnGuideStatementScraper.scrape(stock_code)
        snapshot_parser = FnSnapshotParser()
        statement_parser = FnStatementParser()
        dto = snapshot_parser.parse(stock_code)

        try:
            stmt = statement_parser.parse(stock_code)
            dto.annual_statements = stmt.annual_statements
            dto.quarter_statements = stmt.quarter_statements

            summary_dao: StockSummaryDAO = dao_factory.get('StockSummaryDAO')
            statement_dao: FnStatementAbbrDAO = dao_factory.get('FnStatementAbbrDAO')

            summary_dao.update(dto.stock_summary)
            statement_dao.update(dto.annual_abbreviations)
            statement_dao.update(dto.quarter_abbreviations)

            if len(stmt.annual_statements) > 0:
                statement_dao.update(dto.annual_statements)
                statement_dao.update(dto.quarter_statements)

        except StatementParseError as err:
            logger.error(err)

        return dto

    def _estimate_prices(self, baseline: DataFrame) -> DataFrame:
        """
        초과이익 계수를 적용하여 매수, 매도, 적정주가를 계산한다.
        :param baseline: 분석 시작년도 DataFrame(요구수익률, 초과이익률, ROE, 지배주주순익, 지배주주지분,..)
        :return:
            DataFrame
        """
        df_result = DataFrame()

        for coefficient in COEFFICIENTS:
            table = self.apply_coefficient(baseline, coefficient['coefficient'])
            pv_of_ri = self.calc_pv_of_ri(table)
            equity_current, equity_std = self.calc_equity(pv_of_ri, table)
            affordable_price = self.calc_price(equity_std)
            per = self.calc_per(equity_current)

            logger.debug(f"초과이익 계수: {coefficient.get('coefficient')}, PV of RI: {pv_of_ri}")

            if logger.isEnabledFor(logging.DEBUG):
                print(tabulate(table, headers="keys", tablefmt="psql", floatfmt=".2f"))

            df = DataFrame({"적정주주가치": [int(equity_current)], "적정주가": [affordable_price], "PER": [per]})
            df.index = [coefficient['label']]
            df['판단'] = coefficient['decision']

            df_result = df_result.append(df)
        return df_result

    def _resolve_roe(self, quarter_roe_df: DataFrame) -> (float, str):
        """
        분석시 적용할 ROE 값을 정한다.
        재무제표가 있으면 ROEEstimator 통해 계산하고, 재무제표 자료가 없으면 컨센서스틀 찾아서 반환한다.
        컨센서스도 없으면 최근분기 ROE 반환
        :param quarter_roe_df: DataFrame, 최근분기 계산값
        :return:
            (ROE 값, ROE 산출방법)
        """
        # 재무제표가 있으면 ROE 값을 추정한다.
        if self.dto.quarter_statements is not None and len(self.dto.annual_statements) > 0:
            roe_analyzer = ROEEstimator()
            roe_analyzer.estimate(self.ticker.code, statement_dto=self.dto)
            return roe_analyzer.estimated_roe, 'analyzed'

        roe = self.db_helper.find_recent_consensus_roe(self.ticker.code)
        if roe is not None:
            return roe, 'consensus'

        roe = quarter_roe_df.loc['ROE', quarter_roe_df.columns[0]]

        return roe, 'quarter'

    def create_baseline(self, apply_roe):
        """
        RIM 적정주가 추정을 위한 기준 데이터를 만들어서 반환한다.
        +---------+-----------------+
        |         |   2022          |
        |---------+-----------------|
        | 요구수익률   |        7.89 |
        | 초과이익률   |        6.63 |
        | ROE     |           14.52 |
        | 지배주주순이익 |        nan |
        | 지배주주지분  | 3.21519e+06 |
        | 초과이익    |          nan |
        +---------+-----------------+
        :return: DataFrame
        """

        # 초과이익률 = 적용 ROE - 요구수익률
        excess_profit_rate = apply_roe - self.req_profit_rate

        # ROE = 초과수익률 + 요구수익률
        roe = excess_profit_rate + self.req_profit_rate
        df = DataFrame({
            self.std_date.year: [
                round(self.req_profit_rate, 2),
                round(excess_profit_rate, 2),
                roe,
                None,
                self.equity_on_std_date,
                None
            ]
        }, index=["요구수익률", "초과이익률", "ROE", "지배주주순이익", "지배주주지분", "초과이익"])

        return df

    @staticmethod
    def apply_coefficient(baseline: DataFrame, coefficient: float):
        """
        분석 년수만큼 초과이익 계수를 적용한 계산 결과를 반환한다.
        :param baseline: DataFrame, 기준시점 자료
        :param coefficient: 초과이익 계수
        :return:
            DataFrame
        """
        df = baseline.astype(float)

        for i in range(0, ANALYSIS_YEARS):
            year = df.columns[i] + 1

            req_profit_rate = df.loc["요구수익률", df.columns[i]]
            excess_profit_rate = df.loc["초과이익률", df.columns[i]] * coefficient
            roe = round(req_profit_rate + excess_profit_rate, 2)

            # 지배주주 순이익
            controlling_income = round(df.loc["지배주주지분", df.columns[i]] * roe / 100, 2)

            # 지배주주 지분
            controlling_interest = round(df.loc["지배주주지분", df.columns[i]] + controlling_income, 2)

            # 초과이익
            excess_profit = round(controlling_income - df.loc["지배주주지분", df.columns[i]] * req_profit_rate / 100, 2)

            df[year] = [req_profit_rate, excess_profit_rate, roe, controlling_income, controlling_interest,
                        excess_profit]

        return df

    def resolve_time_factor(self, roe: float):
        """
        분석기준 시점, 종료시점, 기준시점 지배주주지분을 결정한다.
        :return:
        """
        controlling_interest, column_date = self.select_fact(roe)

        # 분석 기준일자
        std_ym = datetime.strptime(column_date, '%Y/%m')
        last_day = calendar.monthrange(std_ym.year, std_ym.month)[1]
        std_date = datetime.strptime(f"{std_ym.year}/{std_ym.month}/{last_day}", "%Y/%m/%d")

        # 기준시점 - 현재
        today = datetime.today()
        date_diff = days_between(today, std_date)

        # 분석종료 일자
        fiscal_year = self.quarter_fiscal_year - 1
        year_count = 10
        if std_date.month != 12:
            year_count = 11
        analysis_end_date = datetime.strptime(f"{fiscal_year + year_count}/{std_date.month}/{std_date.day}", "%Y/%m/%d")
        logger.debug(
            f"분석기준일자: {std_date}, 기준시점-현재: {date_diff}일, 분석종료일자: {analysis_end_date}, 분석기준일자 주주지분: {controlling_interest}")

        self.std_date = std_date
        self.days_elapsed = date_diff
        self.equity_on_std_date = controlling_interest

    def select_fact(self, roe) -> (float, str):
        """
        분석기준 시점, 종료시점, 기준시점 지배주주지분을 결정을 위해
        적용 ROE값과 일치하는 분기/연간 자료가 있는지 확인한다.
        :param roe: 적용 ROE
        :return:
            지배주주지분, 회계일자
        """
        date = None
        """ 분석자료 중에서 roe가 추정 ROE와 같은 컬럼을 찾는다. """
        column = self.fact_table.loc['ROE', self.fact_table.columns[self.fact_table.eq(roe).any()]]
        if len(column) > 0:
            date = column.index[0]

        # 추정 ROE 값과 일치하는 컬럼을 못찾은 경우는 최근 4분기 자료 사용
        if date is None:
            logger.debug(f'적용 ROE와 일치하는 항목 못찾음: {roe}')
            controlling_interest = self.fact_table.loc['지배주주지분', self.fact_table.columns[-1]]
            column_date = self.fact_table.columns[-1]
        else:
            logger.debug(f'추정 ROE와 일치하는 항목 찾음: {roe}')
            controlling_interest = self.fact_table.loc['지배주주지분', date]
            controlling_income = self.fact_table.loc['지배주주순이익', date]
            column_date = date

            if math.isnan(controlling_interest) or math.isnan(controlling_income):
                logger.info(f"적용 ROE와 일치하는 항목을 찾았으나 '지배주주기분' 또는 '지배주주순이익' 자료 없음. 최근분기 자료로 대체")
                controlling_interest = self.fact_table.loc['지배주주지분', self.fact_table.columns[-1]]
                column_date = self.fact_table.columns[-1]

        return controlling_interest, column_date

    def calc_equity(self, pv_of_ri, table):
        """
        현재, 분석시점 기준 주주가치(지배주주지분)를 계산해서 반환한다.
        :param pv_of_ri: 미래 잔여이익의 현재가치
        :param table: DataFrame, 분석기간(10년) 초과이익 계수가 적용된 DataFrame
        :return:
            현재기준 주주가치, 분석시점 기준 주주가치
        """

        # 주주가치(분석시점 기준)
        equity_std = round(table.loc["지배주주지분", table.columns[0]] + pv_of_ri, 2)

        # 주주가치(현재 기준)
        equity_current = round(self.calc_current_value(equity_std), 2)
        logger.debug(f"주주가치(분석시점기준): {format_with(equity_std)}, "
                     f"주주가치(현재기준): {format_with(equity_current)}")

        return equity_current, equity_std

    def calc_current_value(self, price_std):
        """
        현재기준 가치 계산
        기준값 / (1 + 요구수익률) ^ (기준시점부터 경과일수 / 365)
        :param price_std: 분석 기준시점 RIM 적정 주가
        :return:
        """
        current = price_std / (1 + (self.req_profit_rate / 100)) ** (self.days_elapsed / 365)
        return current

    def calc_pv_of_ri(self, table):
        """
        미래 잔여이익(future RI)의 현재가치(PV)
        :param table:
        :return:
        """
        excess_profit_list = list(table.loc["초과이익"].fillna(0))
        pv_of_ri = self.npv_excel(self.req_profit_rate / 100, excess_profit_list[1:])
        # logger.debug(f"PV of RI: {pv_of_ri}")
        return pv_of_ri

    @staticmethod
    def npv_excel(rate, values):
        """
        순현재 가치(NPV)를 엑셀 방식으로 계산한다.
        :param rate:
        :param values:
        :return:
        """
        values = numpy.asarray(values)
        return (values / (1 + rate) ** numpy.arange(1, len(values) + 1)).sum(axis=0)

    def calc_price(self, equity_std):
        """
        RIM 적정주가 계산
        기준시점 적정주가 = 기준시점 지배주주지분 * 1억 / (보통주 + 우선주 - 자기주식)
        :param equity_std: 분석시점 기준 주주가치(지배주주지분)
        :return:
        """
        # RIM 적정주가(분석시점 기준)
        summary = self.dto.stock_summary
        stock_cnt = summary.common_stock_cnt + summary.pref_stock_cnt - summary.treasury_stock_cnt
        # logger.debug(f"발행주식수: {self.fact.dto.stock_summary.common_stock_cnt}, 자기주식: {}")
        affordable_price_std = equity_std * 100000000 / stock_cnt
        affordable_price_std = int(affordable_price_std)

        # RIM 적정주가(현재 기준)
        affordable_price_current = int(self.calc_current_value(affordable_price_std))
        logger.debug(f"RIM 적정주가(분석시점기준): {format_with(affordable_price_std)}, "
                     f"RIM 적정주가(현재기준): {format_with(affordable_price_current)}")

        return affordable_price_current

    def calc_per(self, equity):
        per = None
        try:
            profit = self.fact_table.loc["지배주주순이익", self.fact_table.columns[4]]
            per = round(equity / profit, 2)
        except (TypeError, KeyError, ValueError) as err:
            logger.warning(f"PER 계산 불가: {err}")

        return per
