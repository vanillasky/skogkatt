import pytest

from skogkatt.conf.app_conf import get_project_path


@pytest.fixture(scope="module")
def fn_dto(request):
    from skogkatt.crawler.fnguide.parser import FnStatementParser

    stock_code = getattr(request.module, "stock_code", "005930")
    file_type = getattr(request.module, "file_type", "005930")
    statement_html = get_project_path().joinpath(f'tests/fnguide/fixture/fn_{file_type}_{stock_code}.html')

    if not statement_html.exists():
        raise ValueError(f'File not exists: {statement_html}')

    """ html 파일을 DTO로 파싱 """
    statement_parser = FnStatementParser()

    dto = statement_parser.parse(stock_code, statement_html)

    yield dto
