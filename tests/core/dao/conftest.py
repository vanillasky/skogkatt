import pytest

from skogkatt.tests.fnguide.sample_html_generator import load_html


@pytest.fixture(scope="module")
def fn_dto(request):
    from skogkatt.crawler.fnguide.parser import FnSnapshotParser, FnStatementParser

    stock_code = getattr(request.module, "stock_code", "005930")

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

    yield dto
