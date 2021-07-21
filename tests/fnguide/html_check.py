import pandas as pd
from tabulate import tabulate

from skogkatt.conf.crawl_conf import FN_SNAPSHOT_URL, FN_STATEMENT_URL
from skogkatt.crawler.util import scrape, remove_tag


def find_tables_by_caption(soup, caption_value: str):
    tables = []
    for caption in soup.find_all('caption'):
        if caption.get_text() == caption_value:
            tables.append(caption.find_parent('table'))

    return tables


def print_snapshot_tables(stock_code, file=None):
    payload = {
        'pGB': '1',
        'gicode': 'A' + stock_code,
        'cID': '',
        'MenuYn': 'Y',
        'ReportGB': 'D',
        'NewMenuID': '11',
        'stkGb': '701'
    }

    soup = scrape(FN_SNAPSHOT_URL, payload) if file is None else read_from(file)
    # tables = soup.find_all("table")
    summary_tables = find_tables_by_caption(soup, "Financial Highlight")
    print(f'Financial Highlight tables: {len(summary_tables)}')
    for i in range(len(summary_tables)):
        remove_tag(summary_tables[i], "span", "csize")
        df = pd.read_html(str(summary_tables[i]), header=1)[0]
        print(f"Table[{i}]")
        print(tabulate(df, headers="keys", tablefmt="psql"))

    annual_df = pd.read_html(str(summary_tables[1]), header=1)[0]   # 연결 - 연간
    quarter_df = pd.read_html(str(summary_tables[2]), header=1)[0]  # 연결 - 분기
    quarter_sep_df = pd.read_html(str(summary_tables[5]), header=1)[0]  # 별도 - 분기


def print_statement_tables(stock_code, file=None):
    payload = {
        'pGB': '1',
        'gicode': 'A' + stock_code,
        'cID': '',
        'MenuYn': 'Y',
        'ReportGB': 'D',
        'NewMenuID': '11',
        'stkGb': '701'
    }

    soup = scrape(FN_STATEMENT_URL, payload) if file is None else read_from(file)
    tables = soup.find_all("table")

    for i in range(len(tables)):
        remove_tag(tables[i], "span", "csize")
        df = pd.read_html(str(tables[i]), header=0)[0]
        print(f"Table[{i}]")
        print(tabulate(df, headers="keys", tablefmt="psql"))


if __name__ == '__main__':
    # print_snapshot_tables("002210")
    print_statement_tables("002210")

