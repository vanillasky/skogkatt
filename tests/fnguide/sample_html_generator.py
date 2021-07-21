import requests
from bs4 import BeautifulSoup

from skogkatt.conf.app_conf import get_project_path

URL_SNAPSHOT = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp'
URL_STATEMENT = 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp'

"""
FnGuide 스냅샵, 재무제표 페이지를 파일로 저장
"""


def save_file(url, params, file_path):
    res = requests.get(url, params=params)
    soup = BeautifulSoup(res.content, "html5lib")

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))


def get_payload(stock_code):
    return {
        'pGB': '1',
        'gicode': 'A' + stock_code,
        'cID': '',
        'MenuYn': 'Y',
        'ReportGB': '',
        'NewMenuID': '11',
        'stkGb': '701'
    }


def load_html(stock_code, file_type='snapshot'):
    html_file = get_project_path().joinpath(f'tests/fnguide/fn_{file_type}_sample_{stock_code}.html')
    if not html_file.exists():
        if file_type == 'snapshot':
            save_file(URL_SNAPSHOT, get_payload(stock_code), html_file)
        elif file_type == 'statement':
            save_file(URL_STATEMENT, get_payload(stock_code), html_file)
        else:
            raise ValueError(f'Not supported file type: {file_type}')

    return html_file


if __name__ == '__main__':

    stock_codes = ['005930']
    path = get_project_path()

    for code in stock_codes:
        payload = get_payload(code)

        fn_snapshot_file = path.joinpath(f'tests/fnguide/fn_snapshot_sample_{code}.html')
        save_file(URL_SNAPSHOT, payload, file_path=fn_snapshot_file)

        fn_statement_file = path.joinpath(f'tests/fnguide/fn_statement_sample_{code}.html')
        save_file(URL_STATEMENT, payload, file_path=fn_statement_file)
