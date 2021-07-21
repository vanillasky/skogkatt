from pathlib import Path
import pandas as pd
import pytest

from skogkatt.conf.crawl_conf import FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH
from skogkatt.crawler.util import read_from, remove_tag
from skogkatt.errors import StatementParseError
from skogkatt.tests.fnguide.sample_html_generator import load_html


@pytest.fixture
def parser(request):
    from skogkatt.crawler.fnguide.parser import FnSnapshotParser

    return FnSnapshotParser()


def test_resolve_file_path(parser):
    snapshot_file_dir = FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH
    stock_code = "005930"

    path = parser.resolve_file_path(stock_code)
    expected = Path(rf'{snapshot_file_dir}\fn_snapshot_005930.html')
    assert (expected == path)


def test_parse(parser):
    htmls = {}
    htmls['005930'] = load_html('005930', file_type='snapshot')     # 삼성전자
    # htmls['153360'] = load_html('153360', file_type='snapshot')     # 하이골드3호
    # htmls['000060'] = load_html('000060', file_type='snapshot')     # 메리츠화재
    # htmls['003540'] = load_html('003540', file_type='snapshot')     # 대신증권
    # # htmls['003540'] = load_html('002210', file_type='snapshot')     # 동성제약

    for stock_code, html in htmls.items():
        dto = parser.parse(stock_code, file=html)

        # for stmt in dto.annual_statements:
        #     print(tabulate(stmt.to_dataframe(), headers="keys", tablefmt="psql"))

        summary = dto.stock_summary
        assert (stock_code == summary.stock_code)
        assert(8 == len(dto.annual_abbreviations))
        assert(8 == len(dto.quarter_abbreviations))


def test_validate_index(parser):
    invalid_row_index = {
        '매출액': 0, '영업이익': 1, '영업이익(발표기준)': 2, '당기순이익-오류': 3,
        '지배주주순이익': 4, '비지배주주순이익': 5, '자산총계': 6, '부채총계-오류': 7,
        '자본총계': 8, '지배주주지분': 9, '비지배주주지분': 10, '자본금': 11, '부채비율': 12,
        '유보율': 13,  '영업이익률': 14,  '지배주주순이익률': 15, 'ROA': 16, 'ROE': 17,
        'EPS': 18, 'BPS': 19, 'DPS': 20, 'PER': 21, 'PBR': 22, '발행주식수': 23,
        '배당수익률': 24
    }

    test_stock_code = "005930"
    html_file = load_html(test_stock_code, file_type='snapshot')
    soup = read_from(html_file)
    tables = soup.find_all('table')
    remove_tag(tables[11], "span", "csize")
    remove_tag(tables[12], "span", "csize")

    annual_df = pd.read_html(str(tables[11]), header=1)[0]
    try:
        parser.validate_index(annual_df, invalid_row_index)
    except StatementParseError as err:
        assert True
