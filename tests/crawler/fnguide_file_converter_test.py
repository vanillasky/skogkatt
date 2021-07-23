from typing import List

import pytest
from tabulate import tabulate

from skogkatt.batch import batch_lookup
from skogkatt.batch.queue_factory import queue_factory
from skogkatt.core.dao import dao_factory
from skogkatt.core.financial import Statement
from skogkatt.core.financial.constants import ReportCode
from skogkatt.crawler.fnguide import converter
from skogkatt.tests.fnguide.constants import FNG_STATEMENT_ROW_CNT


@pytest.fixture
def setup(request):
    summary_dao = dao_factory.get('StockSummaryDAO')
    statement_dao = dao_factory.get('FnStatementDAO')
    stmt_abbr_dao = dao_factory.get('FnStatementAbbrDAO')

    def teardown():
        pass
        statement_table = statement_dao.get_table_name()
        statement_dao.get_engine().get_db().drop_collection(statement_table)

        statement_abbr_table = stmt_abbr_dao.get_table_name()
        stmt_abbr_dao.get_engine().get_db().drop_collection(statement_abbr_table)

        summary_table = summary_dao.get_table_name()
        summary_dao.get_engine().get_db().drop_collection(summary_table)

    request.addfinalizer(teardown)

    return summary_dao, statement_dao, stmt_abbr_dao


@pytest.fixture
def failed_dao(request):
    failed_ticker_dao = dao_factory.get('FailedTickerDAO')

    def teardown():
        table = failed_ticker_dao.get_table_name()
        failed_ticker_dao.get_engine().get_db().drop_collection(table)

    request.addfinalizer(teardown)

    return failed_ticker_dao


def test_convert_snapshot(setup):

    summary_dao, statement_dao, stmt_abbr_dao = setup

    # 삼성전자, LG화학
    stock_codes = ['005930', '051910']
    job_name = batch_lookup.FN_SNAPSHOT_CONVERT['name']
    queue = queue_factory.assign_queue(job_name, stock_codes)

    # 데이터 변환
    processed_stock_codes = converter.convert_snapshot(queue)
    assert (2 == len(processed_stock_codes))
    assert queue_factory.get_queue(job_name).empty()

    # 변환 자료 DB 조회
    summary_dao = dao_factory.get('StockSummaryDAO')
    summaries = summary_dao.find(stock_codes=stock_codes)
    assert (2 == len(summaries))

    annual_abbr = stmt_abbr_dao.find(stock_code="005930", report_code=ReportCode.summary_annual)
    assert (5 <= len(annual_abbr))

    quarter_abbr = stmt_abbr_dao.find(stock_code="005930", report_code=ReportCode.summary_quarter)
    assert (5 <= len(quarter_abbr))


def test_convert_statement(setup):
    summary_dao, statement_dao, stmt_abbr_dao = setup

    # 삼성전자, LG화학
    stock_codes = ['005930', '051910']
    job_name = batch_lookup.FN_STATEMENT_CONVERT['name']
    queue = queue_factory.assign_queue(job_name, stock_codes)

    # 데이터 변환
    processed_stock_codes = converter.convert_statement(queue)
    assert (2 == len(processed_stock_codes))
    assert queue_factory.get_queue(job_name).empty()

    annuals: List[Statement] = statement_dao.find(stock_code="005930", report_code=ReportCode.annual)
    quarters = statement_dao.find(stock_code="005930", report_code=ReportCode.quarter)

    assert (3 == len(annuals))
    for stmt in annuals:
        assert (FNG_STATEMENT_ROW_CNT, len(stmt.facts))

    assert (4 == len(quarters))
    for stmt in quarters:
        assert (FNG_STATEMENT_ROW_CNT, len(stmt.facts))


def test_convert_failure(failed_dao):
    dao = failed_dao

    # 메리츠화재, 대신증권
    stock_codes = ['000060', '003540']
    job_name = batch_lookup.FN_STATEMENT_CONVERT['name']
    queue = queue_factory.assign_queue(job_name, stock_codes)

    # 데이터 변환
    processed_stock_codes = converter.convert_statement(queue)
    assert (0 == len(processed_stock_codes))
    assert queue_factory.get_queue(job_name).empty()

    result = dao.find(job_name=job_name)
    assert (2 == len(result))