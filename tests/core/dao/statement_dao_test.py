import pytest
from tabulate import tabulate

from skogkatt.commons.util.date import get_annual_periods
from skogkatt.conf.app_conf import app_config, Config
from skogkatt.core.financial.constants import ReportCode
from skogkatt.crawler.fnguide.index import FN_HIGHLIGHT_ROW_INDEX

from skogkatt.tests.fnguide.constants import FNG_STATEMENT_ROW_CNT
from skogkatt.tests.fnguide.sample_html_generator import load_html

app_config.set_mode(Config.TEST)


@pytest.fixture
def dao():
    from skogkatt.core.dao import dao_factory
    return dao_factory.get('FnStatementDAO')


@pytest.fixture
def abbr_dao():
    from skogkatt.core.dao import dao_factory
    return dao_factory.get('FnStatementAbbrDAO')


@pytest.fixture
def setup(dao, request):
    from skogkatt.crawler.fnguide.parser import FnSnapshotParser, FnStatementParser

    stock_code = "005930"
    """ FnGuide 스냅샷, 제무재표 html 파일 로딩, 없으면 comp.fnguide.com 에서 크롤 """
    snapshot_html = load_html(stock_code, file_type='snapshot')
    statement_html = load_html(stock_code, file_type='statement')

    """ html 파일을 DTO로 파싱 """
    snapshot_parser = FnSnapshotParser()
    statement_parser = FnStatementParser()

    dto = snapshot_parser.parse(stock_code, snapshot_html)
    stmt_dto = statement_parser.parse(stock_code, statement_html)
    dto.annual_statements = stmt_dto.annual_statements
    dto.quarter_statements = stmt_dto.quarter_statements

    yield dto, stock_code

    def teardown():
        statement_dao = dao
        statement_dao.delete()

    request.addfinalizer(teardown)


def test_insert_statement(setup, dao):
    """
    1개년도 재무제표 db insert
    :return:
    """
    dto, stock_code = setup
    inserted = dao.update([dto.annual_statements[0]])
    assert (FNG_STATEMENT_ROW_CNT, inserted)
    assert (inserted, dao.count())


def test_append_new_statement(setup, dao):
    """
    기존재 자료 삭제 후 insert 확인
    연간 자료 1건 업데이트 후 추가로 3년치 업데이트해서 DB자료가 총 3년치인지 확인
    """
    dto, stock_code = setup
    statements = dto.annual_statements
    inserted = dao.update([statements[0]])
    assert (FNG_STATEMENT_ROW_CNT, inserted)

    inserted = dao.update(statements)
    assert (FNG_STATEMENT_ROW_CNT * 3, inserted)


def test_find_statement(setup, dao):
    dto, stock_code = setup
    """ 연간자료 3년치 """
    inserted = dao.update(dto.annual_statements)
    assert (FNG_STATEMENT_ROW_CNT * 3, inserted)

    """ 분기자로는 4년치 """
    inserted = dao.update(dto.quarter_statements)
    assert (FNG_STATEMENT_ROW_CNT * 4, inserted)

    statements = dao.find(stock_code=stock_code, report_code=ReportCode.quarter)
    assert (4,  len(statements))

    for stmt in statements:
        print(tabulate(stmt.to_dataframe(), headers="keys", tablefmt="psql"))


def test_insert_abbreviations(setup, abbr_dao):
    dto, stock_code = setup
    row_cnt = len(FN_HIGHLIGHT_ROW_INDEX)

    inserted = abbr_dao.update(dto.annual_abbreviations)

    # 5개년도 + 3개년도 컨센서스
    assert (row_cnt * 8, inserted)


def test_find_abbreviations(setup, abbr_dao):
    """ FnGuide 스냅샷 자료 조회 테스트 """
    dto, stock_code = setup
    abbr_dao.update(dto.annual_abbreviations)
    abbr_dao.update(dto.quarter_abbreviations)

    annuals = abbr_dao.find(stock_code, ReportCode.summary_annual)
    quarters = abbr_dao.find(stock_code, ReportCode.summary_quarter)
    assert (5 <= len(annuals))
    assert (5 <= len(quarters))

    for stmt in annuals:
        assert (len(FN_HIGHLIGHT_ROW_INDEX), len(stmt.facts))
        # print(tabulate(stmt.to_dataframe(), headers="keys", tablefmt="psql"))

    for stmt in quarters:
        assert (len(FN_HIGHLIGHT_ROW_INDEX), len(stmt.facts))

    annual_consensus = abbr_dao.find(stock_code, ReportCode.summary_annual, consensus=1)
    assert (3 <= len(annual_consensus))
    for stmt in annual_consensus:
        assert (len(FN_HIGHLIGHT_ROW_INDEX), len(stmt.facts))


def test_find_consensus(setup, abbr_dao):
    dto, stock_code = setup
    abbr_dao.update(dto.annual_abbreviations)
    abbr_dao.update(dto.quarter_abbreviations)

    from_ym, to_ym = get_annual_periods(count_years=5)
    consensus = abbr_dao.find(stock_code, ReportCode.summary_annual, from_ym, consensus=1)
    for stmt in consensus:
        print(tabulate(stmt.to_dataframe(), headers="keys", tablefmt="psql"))

    roe_consensus = consensus[-1].get_fact('ROE').value
    print(roe_consensus)

#     # def test_find_recent(self):
#     #     dao = StatementDao()
#     #     statements = dao.find_statement(stock_code=self.test_stock_code, report_code=ReportCode.annual)
#     #     print(tabulate(statements[0].to_dataframe(), headers="keys", tablefmt="psql"))
#     #
#     #     stmts = dao.find_recent_statement(stock_code=self.test_stock_code, report_code=ReportCode.annual)
#
#
