from typing import List

from skogkatt.core.financial import Statement, StockSummary


class FinancialStatementDTO:
    def __init__(self, stock_code: str):
        self._stock_code = stock_code
        self._stock_summary: StockSummary = None
        self._annual_statements: List[Statement] = None
        self._quarter_statements: List[Statement] = None
        self._annual_abbreviations: List[Statement] = None
        self._quarter_abbreviations: List[Statement] = None

    @property
    def stock_code(self):
        return self._stock_code

    @property
    def stock_summary(self):
        return self._stock_summary

    @stock_summary.setter
    def stock_summary(self, stock_summary: StockSummary):
        self._stock_summary = stock_summary

    @property
    def annual_statements(self):
        return self._annual_statements

    @annual_statements.setter
    def annual_statements(self, statements: List[Statement]):
        self._annual_statements = statements

    @property
    def quarter_statements(self):
        return self._quarter_statements

    @quarter_statements.setter
    def quarter_statements(self, statements: List[Statement]):
        self._quarter_statements = statements

    @property
    def annual_abbreviations(self):
        return self._annual_abbreviations

    @annual_abbreviations.setter
    def annual_abbreviations(self, statements: List[Statement]):
        self._annual_abbreviations = statements

    @property
    def quarter_abbreviations(self):
        return self._quarter_abbreviations

    @quarter_abbreviations.setter
    def quarter_abbreviations(self, statements: List[Statement]):
        self._quarter_abbreviations = statements
