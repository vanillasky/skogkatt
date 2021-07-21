import math
from typing import List

from skogkatt.commons.util.date import get_quarter_periods, get_annual_periods
from skogkatt.core.dao import dao_factory
from skogkatt.core.financial import StockSummary, Statement
from skogkatt.core.financial.constants import ReportCode
from skogkatt.core.financial.dto import FinancialStatementDTO
from skogkatt.errors import NoDataFoundError


class DBHelper:
    def __init__(self):
        self.stmt_dao = dao_factory.get("FnStatementDAO")
        self.stmt_abbr_dao = dao_factory.get("FnStatementAbbrDAO")
        self.summary_dao = dao_factory.get("StockSummaryDAO")

    def find_recent_consensus_roe(self, stock_code) -> float or None:
        """
        ROE 컨센서스 값을 찾아서 반환
        :param stock_code: 종목코드
        :return:
        """
        from_date, to_date = get_annual_periods(5)
        consensus = self.stmt_abbr_dao.find(stock_code, ReportCode.summary_annual, from_date, consensus=1)

        if len(consensus) == 0 or consensus is None:
            return None

        roe_consensus = consensus[-1].get_fact('ROE').value
        if math.isnan(roe_consensus):
            return None

        return roe_consensus

    def get_fn_statement_dto(self, stock_code) -> FinancialStatementDTO or None:
        stock_summary = self.summary_dao.find_one(stock_code)
        if stock_summary is None:
            raise NoDataFoundError(f'Stock summary not found: {stock_code}')

        dto = FinancialStatementDTO(stock_code)
        dto.stock_summary = stock_summary

        dto.annual_abbreviations = self.find_fn_abbreviations(stock_code, ReportCode.summary_annual)
        if len(dto.annual_abbreviations) == 0:
            raise NoDataFoundError(f'Financial Snapshot not found: {stock_code}')

        dto.quarter_abbreviations = self.find_fn_abbreviations(stock_code, ReportCode.summary_quarter)

        dto.annual_statements = self.find_fn_statements(stock_code, ReportCode.annual)
        dto.quarter_statements = self.find_fn_statements(stock_code, ReportCode.quarter)

        return dto

    def find_stock_summary(self, stock_code: str) -> StockSummary or None:
        return self.summary_dao.find_one(stock_code)

    def find_fn_abbreviations(self,
                              stock_code: str,
                              report_code: int,
                              from_date: str = None,
                              to_date: str = None) -> List[Statement]:
        """
        DB에서 요약 재무제표를 찾아서 반환한다.
        :param stock_code: str, 종목코드
        :param report_code: int, 연간/분기 구분
        :param from_date: str, optional, 시작년월
        :param to_date: str, optional, 종료년월
        :return:
        """

        if report_code == ReportCode.summary_quarter:
            default_from_ym, default_to_ym = get_quarter_periods(6)
            from_date = default_from_ym if from_date is None else from_date
            to_date = default_to_ym if to_date is None else to_date

        elif report_code == ReportCode.summary_annual:
            default_from_ym, default_to_ym = get_annual_periods(5)
            from_date = default_from_ym if from_date is None else from_date
            to_date = default_to_ym if to_date is None else to_date

        return self.stmt_abbr_dao.find(stock_code, report_code=report_code, from_date=from_date, to_date=to_date)

    def find_fn_statements(self,
                           stock_code: str,
                           report_code: int,
                           from_date: str = None,
                           to_date: str = None) -> List[Statement]:
        """
        DB에서 재무제표를 찾아서 반환한다.
        :param stock_code: str, 종목코드
        :param report_code: int, 연간/분기 구분
        :param from_date: str, optional, 시작년월
        :param to_date: str, optional, 종료년월
        :return:
            List[Statement]
        """
        if report_code == ReportCode.summary_quarter:
            default_from_ym, default_to_ym = get_quarter_periods(5)
            from_date = default_from_ym if from_date is None else from_date
            to_date = default_to_ym if to_date is None else to_date

        elif report_code == ReportCode.summary_annual:
            default_from_ym, default_to_ym = get_annual_periods(5)
            from_date = default_from_ym if from_date is None else from_date
            to_date = default_to_ym if to_date is None else to_date

        return self.stmt_dao.find(stock_code, report_code, from_date, to_date)
