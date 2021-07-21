import pytest
from tabulate import tabulate

from skogkatt.conf.app_conf import get_project_path, app_config, Config
from skogkatt.crawler.fnguide.parser import FnStatementParser
from skogkatt.screeners.rim import ROEEstimator
from skogkatt.tests.fnguide.sample_html_generator import load_html

app_config.set_mode(Config.TEST)
stock_code = "005930"
file_type = "statement"


@pytest.fixture
def setup_db(request):
    from skogkatt.crawler.fnguide.parser import FnSnapshotParser, FnStatementParser

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

    from skogkatt.core.dao import dao_factory
    summary_dao = dao_factory.get('StockSummaryDAO')
    stmt_dao = dao_factory.get('FnStatementDAO')
    summary_dao.update(dto.stock_summary)
    stmt_dao.update(dto.annual_statements)
    stmt_dao.update(dto.quarter_statements)

    yield dto

    def teardown():
        pass
        # summary_dao.delete()
        # stmt_dao.delete()

    request.addfinalizer(teardown)


def test_estimate_roe_with_file(fn_dto):
    """ Test with saved html """
    roe_estimator = ROEEstimator()
    df = roe_estimator.estimate(stock_code, statement_dto=fn_dto)
    print(tabulate(df, headers="keys", tablefmt="psql"))
    roe = roe_estimator.estimated_roe
    assert 10.67 == roe


def test_estimate_roe_with_database(setup_db):
    roe_estimator = ROEEstimator()
    df = roe_estimator.estimate(stock_code)
    print(tabulate(df, headers="keys", tablefmt="psql"))
