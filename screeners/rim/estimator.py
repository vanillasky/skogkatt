import copy
import logging
from typing import List

from pandas import DataFrame
from tabulate import tabulate

from skogkatt.commons.util.date import get_annual_periods, get_quarter_periods
from skogkatt.core import LoggerFactory
from skogkatt.core.dao import dao_factory
from skogkatt.core.financial import Statement
from skogkatt.core.financial.constants import ReportCode
from skogkatt.core.financial.dto import FinancialStatementDTO
from skogkatt.core.ticker import Ticker
from skogkatt.core.ticker.store import ticker_store
from skogkatt.screeners.rim import Criteria

logger = LoggerFactory.get_logger(__name__)


def aggregate_statements(statements: List[Statement]):
    """
    재무제표 attribute별 집계표를 만든다.
    e.g.)
     외부차입: 단기사채 + 단기차입금 + 유동성장기부채 + 사채 + 장기차입금
     운전자산: 재고자산 + 유동생물자산 + 계약자산 + ...
    :param statements: List[Statement], 재무제표 리스트
    :return:
        DataFrame looks like:
        +--------------+-------------------+-------------------+-------------------+------------------+
        | attribute    |           2018/12 |           2019/12 |           2020/12 |           2021/3 |
        |--------------+-------------------+-------------------+-------------------+------------------|
        | 외부차입         |  146672           |  184121           |  202173           | 199727           |
        | 지배주주지분       |       2.40069e+06 |       2.54916e+06 |       2.6767e+06  |      2.65767e+06 |
        | 비지배주주지분      |   76842           |   79649           |   82777           |  85013           |
        | 설비투자         |       1.30308e+06 |       1.40529e+06 |       1.47421e+06 |      1.51134e+06 |
        ...
        ...
    """
    df = DataFrame()

    for stmt in statements:
        df_stmt = stmt.to_dataframe()
        summary = df_stmt.groupby(['attribute'], sort=False)['value'].sum(numeric_only=True)
        df[f'{stmt.fiscal_date}'] = summary

        df.loc['자기자본'] = df.loc['유보이익'] + df.loc['주주투자']
        df.loc['영업부채'] = df.loc['신용조달']
        df.loc['영업용자산'] = df.loc['설비투자'] + df.loc['운전자산']
        df.loc['비영업자산'] = df.loc['금융투자'] + df.loc['여유자금']
        df.loc['비영업이익'] = df.loc['당기순이익'] - df.loc['영업이익'] + df.loc['이자비용'] + df.loc['법인세비용']

    df = df.drop(['유보이익', '주주투자', '금융투자', '여유자금', '기타', '신용조달'], axis=0)

    return df


def calc_interest_cost(df_aggregate, df_matrix):
    """
    1) 이자비용 계산 = 최근분기 외부차입 합계 * 차입이자율(적용값)
    :param df_aggregate:
    :param df_matrix:
    :return:
        float, 이자비용
    """
    borrowing = df_aggregate.loc['외부차입', df_aggregate.columns[-1]]
    rate = df_matrix.loc['차입이자율', 'applied_value'] / 100
    result = borrowing * rate
    return result


def calc_sales_profit(df_aggregate, df_matrix):
    """
    2) 영업이익 = 최근분기 영업용차산 합계(설비투자 + 운전자산) * 영업자산이익률(적용값)
    :return:
    """
    asset = df_aggregate.loc['영업용자산', df_aggregate.columns[-1]]
    rate = df_matrix.loc['영업자산이익률', 'applied_value'] / 100
    result = asset * rate
    return result


def calc_non_sales_profit(df_aggregate, df_matrix):
    """
    3) 비영업이익 = 최근분기 비영업용차산 합계(금융투자 + 여유자금) * 비영업자산이익률(적용값)
    :return:
    """
    asset = df_aggregate.loc['비영업자산', df_aggregate.columns[-1]]
    rate = df_matrix.loc['비영업자산이익률', 'applied_value'] / 100
    result = asset * rate
    return result


def calc_corp_tax(sales_profit, non_sales_profit, interest_cost):
    """
    법인세비용 = (영업이익 + 비영업이익 - 이자비용) * 단계별 세율 적용
    :return:
    """
    target_income = sales_profit + non_sales_profit - interest_cost

    tax = 0
    if target_income <= 2:
        tax = target_income * 0.1
    elif 2 < target_income <= 200:
        tax = target_income * 0.2 - 0.2
    elif 200 < target_income <= 3000:
        tax = target_income * 0.22 - 4.2
    elif target_income > 3000:
        tax = target_income * 0.25 - 94.2

    return tax


def calc_control_holder_net_profit(df_aggregate, net_income):
    """
    6) 지배주주 순이익 = (지배주주순이익(4분기합) / (지배주주순이익(4분기합) + 비지배주주순이익(4분기합))) * 당기순이익
    """
    c_holder_profit = df_aggregate.loc['지배주주순이익', 'sum']
    nc_holder_profit = df_aggregate.loc['비지배주주순이익', 'sum']
    result = (c_holder_profit / (c_holder_profit + nc_holder_profit)) * net_income
    return result


def calc_nc_holder_net_profit(df_aggregate: DataFrame, net_income):
    """
    7) 비지배주주 순이익 = (비지배주주순이익(4분기합) / (지배주주순이익(4분기합) + 비지배주주순이익(4분기합))) * 당기순이익
    :param df_aggregate:
    :param net_income:
    :return:
    """
    c_holder_profit = df_aggregate.loc['지배주주순이익', 'sum']
    nc_holder_profit = df_aggregate.loc['비지배주주순이익', 'sum']
    result = (nc_holder_profit / (nc_holder_profit + c_holder_profit)) * net_income
    return result


class ROEEstimator:

    def __init__(self):
        self.ticker = None
        self.annual_df = None
        self.quarter_df = None
        self.weights = []
        self.applied_values: DataFrame = None
        self.estimated_roe = 0.0
        self.dto: FinancialStatementDTO = None
        self.summary_dao = dao_factory.get("StockSummaryDAO")
        self.statement_dao = dao_factory.get("FnStatementDAO")

    def estimate(self, stock_code, criteria: Criteria = None, statement_dto: FinancialStatementDTO = None):
        """
        재무제표 집계표를 기반으로 미래 ROE 값을 추정한다
        0) 해당 종목 재무제표 조회. 최근 4년, 4분기: FinancialStatementDTO
           - 재무제표 statement_dto 가 전달되는 경우에는 이 DTO를 사용 DB 조회 생략.
        1) 추정 조건 결정: 가중평균 or 최근 4분기
        2) 재무제표 집계표 만들기. 계산 편의를 위해 그룹별로 묶어서 단순화한 연간, 분기 재무제표 만들기
        3) 집계표에 계산 항목 추가
        4) 추정 조건 적용해서 계산

        :param stock_code: str, 종목코드
        :param criteria: optional, Criteria, 추정 조건: 가중평균 or 최근 4분기
        :param statement_dto: optional, FinancialStatementDTO, 재무제표
        :return:
            DataFrame, looks like:
            +----------+-----------+-----------+-----------------+--------+------------+-----------------+
            |          |   2019/12 |   2020/12 |   최근4분기(2021/3) |   가중평균 | criteria   |   applied_value |
            |----------+-----------+-----------+-----------------+--------+------------+-----------------|
            | 가중치      |      1    |      0.5  |            3    |        | nan        |                 |
            | 영업자산이익률  |     12.37 |     15.75 |           16.81 |  15.71 | 가중평균       |         15.71   |
            | 비영업자산이익률 |      2.76 |      0.68 |            0.66 |   1.13 | 가중평균       |          1.13   |
            | 차입이자율    |      4.15 |      3.02 |            2.94 |   3.22 | 가중평균       |          3.22   |
            | 지배주주 ROE |      8.69 |      9.99 |           10.73 |  10.19 | nan        |         10.6693 |
            +----------+-----------+-----------+-----------------+--------+------------+-----------------+
        """
        if criteria is None:
            criteria = Criteria(default_option="가중평균")
        self.ticker = ticker_store.find_by_stock_code(stock_code)

        dto = statement_dto if statement_dto is not None else self.get_fn_dto(self.ticker)

        self._aggregate(dto)

        result_df = self._prepare_dataframe(dto)
        self._append_factor_to(result_df, '영업자산이익률', '영업이익', '영업용자산')
        self._append_factor_to(result_df, '비영업자산이익률', '비영업이익', '비영업자산')
        self._append_factor_to(result_df, '차입이자율', '이자비용', '외부차입')
        self._append_factor_to(result_df, '지배주주 ROE', '지배주주순이익', '자기자본')

        result_df = self.apply_criteria(criteria, result_df)
        self.estimated_roe = result_df.loc['지배주주 ROE', 'applied_value']

        return result_df

    def _aggregate(self, dto: FinancialStatementDTO):
        """
        연간, 분기 재무제표에서 필요한 항목을 추출해서 각각 DataFrame을 만든다.
        :param dto:
        :return:
        """
        # 연간 자료에 최근분기 데이터 추가
        annual_statements = copy.deepcopy(dto.annual_statements)
        annual_statements.append(dto.quarter_statements[-1])

        self.annual_df = aggregate_statements(annual_statements)
        self.quarter_df = aggregate_statements(dto.quarter_statements)

        # 분기 자료에 계정별 4분기 합 추가
        self.quarter_df['sum'] = self.quarter_df.sum(axis=1, skipna=True)

    def _prepare_dataframe(self, dto):
        columns = self._make_column_headers()
        df = DataFrame(columns=columns)
        self.weights = self._resolve_weights()
        df.loc['가중치'] = self.weights
        df['가중평균'] = None
        # print(tabulate(df, headers="keys", tablefmt="psql"))
        return df

    def _make_column_headers(self):
        """
        ROE 분석용 DataFrame 생성을 위한 컬럼명을 만들어서 반환한다.
        :return:
            List[column_name]
            e.g. ['2018/12', '2019/12, '2020/12', '최근4분기(2020/09)', '가중평균']
        """
        columns = self.annual_df.columns.values.tolist()[1:]
        columns[-1] = f'최근4분기({columns[-1]})'

        return columns

    def _resolve_weights(self):
        """
        가중평균 계산시 사용할 전년도 가중평균을 계산해서
        전전년도, 전년도, 올해 가중치 값을 반환한다.
        :param annual_df: DataFrame, 재무제표 집계(연간)
        :return:
            List[전전연도, 전년도, 올해]
        """
        dates = self.annual_df.columns.values.tolist()
        closing_month = int(dates[-2].split('/')[1])  # 결산월
        recent_month = int(dates[-1].split('/')[1])  # 최종월
        month_elapsed = (recent_month + 12 - closing_month) % 12  # 결산후 개월
        weight = month_elapsed / 6

        logger.debug(f'결산월: {closing_month}, 최종월: {recent_month}, 결산후 개월: {month_elapsed}, 전년도 가중치: {weight}')
        return [1.0, weight, 3.0]

    def _append_factor_to(self, df: DataFrame, factor: str, numerator: str, denominator: str):
        """
        DataFrame에 계산 항목을 추가한다.

        영업자산 이익률(연간) = 당해년도 영업이익 * 2 / (당해년도 영업용자산 + 전년도 영업용자산)
        비영업자산이익률(연간) = 당해년도 비영업이익 * 2 / (당해년도 비영업자산 + 전년도 비영업자산)
        차입이자율(연간) = 당해년도 이자비용 * 2 / (당해년도 외부차입 + 전년도 외부차입)
        지배주주ROE(연간) = 당해년도 지배주주순이익 * 2 / (당해년도 자기자본 + 전년도 자기자본)

        영업자산 이익률(최근4분기) =  4분기합 영업이익 * 2 / (연간제표.최근분기 영업용자산 + 분기자료.최초분기 영업용자산)
        ...

        영업자산 이익률(가중평균) = sum(년도별 영업자산 이익률 * 해당년도 가중평균) / 가중평균값 합계

        :param df: 집계항목을 추가할 DataFrame
        :param factor: str, 집계표에 추가할 항목명
        :param numerator: str, 계산시 분모 항목명
        :param denominator: str, 계산시 분자 항목명
        :return:
        """
        df.loc[factor, df.columns[0]] = self.mean_annual(numerator, denominator, 1, 0)
        df.loc[factor, df.columns[1]] = self.mean_annual(numerator, denominator, 2, 1)
        df.loc[factor, df.columns[2]] = self.mean_recent_quarter(numerator, denominator)
        df.loc[factor, df.columns[3]] = self.weighted_average(df, factor)

        return df

    def mean_annual(self, numerator: str, denominator: str, first_index: int, second_index: int):
        """
        전년도, 올햬 값으로 적용할 항목을 계산합다.
        e.g.) 영업자산 이익률 = 당해년도 영업이익 * 2 / (당해년도 영업용자산 + 전년도 영업용자산)
        :param numerator: 분자 항목, DataFrame의  index
        :param denominator: 분모 항목, DataFrame의 항목 index
        :param first_index: int, 전년도 컬럼 인덱스
        :param second_index: int, 올해 컬럼 인덱스
        :return:
        """
        operating_profit = self.annual_df.loc[numerator, self.annual_df.columns[first_index]]
        asset = self.annual_df.loc[denominator, self.annual_df.columns[first_index]]
        asset_prev_year = self.annual_df.loc[denominator, self.annual_df.columns[second_index]]

        try:
            result = round((operating_profit * 2 / (asset + asset_prev_year) * 100), 2)
        except ZeroDivisionError as err:
            return 0

        return result

    def mean_recent_quarter(self, numerator: str, denominator: str):
        """
        최근4분기 값으로 적용할 항목을 계산한다
        e.g.) 최근4분기 영업자산 이익률 = 4분기합 영업이익 * 2 / (연간자료.최근 영업용자산 + 분기자료.최초 영업용자산)
        :param numerator: 분자 항목
        :param denominator: 분모 항목
        :return:
            float, 최근4분기 적용 계산값
        """

        numerator = self.quarter_df.loc[numerator, 'sum'] * 2
        denominator = (self.annual_df.loc[denominator, self.annual_df.columns[-1]] +
                       self.quarter_df.loc[denominator, self.quarter_df.columns[0]])
        try:
            result = round((numerator / denominator * 100), 2)
        except ZeroDivisionError:
            return 0

        return result

    def weighted_average(self, df: DataFrame, factor: str) -> float:
        """
        가중평균 값을 계산해서 반환한다.
        :param df: 계산 대상 DataFrame
        :param factor: 계산할 항목
        :return:
            float, 가중평균 값
        """
        #  (roa_1 * weights[0] + roa_2 * weights[1] + roa_3 * weights[2]) / sum(weights)
        result = 0

        for i in range(len(self.weights)):
            value = df.loc[factor, df.columns[i]]
            result = result + value * self.weights[i]

        return round(result / sum(self.weights), 2)

    def get_fn_dto(self, ticker: Ticker):
        stock_summary = self.summary_dao.find_one(ticker.code)
        if stock_summary is None:
            raise ValueError(f'Stock summary not found, {ticker.code}({ticker.name}), {ticker.industry}')

        dto = FinancialStatementDTO(ticker.code)
        dto.stock_summary = stock_summary

        from_ym, to_ym = get_annual_periods(5)
        dto.annual_statements = \
            self.statement_dao.find(ticker.code, report_code=ReportCode.annual, from_date=from_ym, to_date=to_ym)

        from_ym, to_ym = get_quarter_periods(5)
        dto.quarter_statements = \
            self.statement_dao.find(ticker.code, report_code=ReportCode.quarter, from_date=from_ym, to_date=to_ym)

        return dto

    def apply_criteria(self, criteria: Criteria, df: DataFrame):
        """
        계산조건을 적용하여 ROE 값 계산
        :param criteria: Criteria, 계산조건(가중평균 or 최근4분기)
        :param df: DataFrame,
            집계된 영업자산이익률, 비영업자산이익률, 차입이자율 자료
        :return:
            DataFrame, ROE 분석 결과
        """

        df = criteria.apply(df)
        """ 이자비용 """
        interest_cost = calc_interest_cost(self.annual_df, df)

        """ 영업이익 """
        sales_profit = calc_sales_profit(self.annual_df, df)

        """ 비영업이익 """
        non_sales_profit = calc_non_sales_profit(self.annual_df, df)

        """ 법인세 비용"""
        tax = calc_corp_tax(sales_profit, non_sales_profit, interest_cost)

        """ 당기순이익 """
        net_income = sales_profit + non_sales_profit - interest_cost - tax

        """ 지배주주 순이익 """
        ctrl_profit = calc_control_holder_net_profit(self.quarter_df, net_income)

        """ 비지배주주 순이익 """
        non_ctrl_profit = calc_nc_holder_net_profit(self.quarter_df, net_income)

        """ ROE """
        roe = ctrl_profit / self.annual_df.loc['자기자본', self.annual_df.columns[-1]] * 100

        df.loc['지배주주 ROE', 'applied_value'] = round(roe, 2)

        data = {
            '적용값':
                {'이자비용': interest_cost,
                 '영업이익': sales_profit,
                 '비영업이익': non_sales_profit,
                 '법인세비용': tax,
                 '당기순이익': net_income,
                 '지배주주순이익': ctrl_profit,
                 '비지배주주순이익': non_ctrl_profit,
                 'ROE 분석값': roe}
        }

        self.applied_values = DataFrame.from_dict(data)
        self.applied_values.index.name = f'{self.ticker.name}({self.ticker.code})'
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(tabulate(self.applied_values, headers="keys", tablefmt="psql"))

        return df
