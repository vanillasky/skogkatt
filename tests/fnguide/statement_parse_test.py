import unittest

import pytest
from tabulate import tabulate

# from skogkatt.conf.app_conf import app_config, Config
# from skogkatt.crawler.fnguide.index import STATEMENT_SECTORS
# from skogkatt.core.financial.constants import StatementType, ReportCode
# from tests.fnguide.constants import FNG_STATEMENT_COL_CNT
# from tests.fnguide.sample_html_generator import load_html
#
#
# class StatementParseTestCase(unittest.TestCase):
#     def setUp(self) -> None:
#         app_config.set_mode(Config.TEST)
#         from skogkatt.core.crawler.fnguide.parser import FnStatementParser
#
#         self.parser = FnStatementParser()
#         self.stock_code = '005930'
from skogkatt.core.financial.constants import StatementType, ReportCode
from skogkatt.crawler.fnguide.index import STATEMENT_SECTORS
from skogkatt.crawler.fnguide.parser import prepare_statements
from skogkatt.tests.fnguide.constants import FNG_STATEMENT_COL_CNT
from skogkatt.tests.fnguide.sample_html_generator import load_html


@pytest.fixture
def parser(request):
    from skogkatt.crawler.fnguide.parser import FnStatementParser

    parser = FnStatementParser()

    return parser, request.param


@pytest.mark.parametrize('parser', ['005930'], indirect=['parser'])
def test_classify_reports(parser):
    parser, stock_code = parser
    parser = init_parser(parser, stock_code)

    expected = ['BS', 'IS', 'CF']
    assert (expected == list(parser.annual_reports.keys()))


@pytest.mark.parametrize('parser', ['005930', '051910'], indirect=['parser'])
def test_prepare_statements(parser):
    parser, stock_code = parser
    parser = init_parser(parser, stock_code)
    reports = parser.annual_reports

    """ DataFrame으로 변환된 재무상태표 """
    dates = reports.get(StatementType.BS).columns[1:5].tolist()
    assert (4 == len(dates))

    """ 변환된 List[Statement] """
    """ 연간 데이터 처리시 12월 자료만 생성하므로 Statement 개수는 3 """
    statements = prepare_statements(stock_code, dates, ReportCode.annual)
    assert (3 == len(statements))
    assert (dates[0] == f'{statements[0].fiscal_date}')


@pytest.mark.parametrize('parser', ['005930', '051910'], indirect=['parser'])
def test_parse_fn_statement(parser):
    """ 재무제표가 DTO로 제대로 파싱되는지 확인 """
    # 153360 - 하이골드3호, 에러: 펀드
    # 000060 - 메리츠 화재, 에러: 보험업
    # 003540 - 대신증권, 에러: 증권
    parser, stock_code = parser
    html = load_html(stock_code, file_type='statement')
    dto = parser.parse(stock_code, file=html)

    # print(len(dto.annual_statements))
    # for stmt in dto.annual_statements:
    #     print(tabulate(stmt.to_dataframe(), headers="keys", tablefmt="psql"))

    assert (3, len(dto.annual_statements))
    recent_statement = dto.annual_statements[-1]
    df = recent_statement.to_dataframe()
    print(tabulate(df, headers="keys", tablefmt="psql"))
    assert (get_row_count(), df.shape[0])
    assert (FNG_STATEMENT_COL_CNT, df.shape[1])


def init_parser(parser, stock_code):
    html = load_html(stock_code, file_type='statement')
    tables = parser._prepare_statement_tables(stock_code, file=html)
    parser.classify_reports(tables)
    return parser


def get_row_count():
    """ 재무제표 자료 행개수를 계산해서 반환한다. """
    """ crawler.fnguide.index.py 참조 """
    income_rows = len(STATEMENT_SECTORS.get('income').values())
    cash_flow_rows = len(STATEMENT_SECTORS.get('cash_flow').values())
    financing_rows = 0
    investment_rows = 0

    for attributes in STATEMENT_SECTORS.get('financing').values():
        financing_rows += len(attributes.values())

    for attributes in STATEMENT_SECTORS.get('investment').values():
        investment_rows += len(attributes.values())

    print(f'income: {income_rows}, cash_flow: {cash_flow_rows}, financing: {financing_rows}, investment:{investment_rows}')
    print(f'total rows: {(income_rows + cash_flow_rows + financing_rows + investment_rows)}')
    return income_rows + cash_flow_rows + financing_rows + investment_rows

