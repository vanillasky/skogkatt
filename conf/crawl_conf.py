PROXIES = {
    'http': 'http://127.0.0.1:8118',
    'https': 'https://127.0.0.1:8118',
}

# FnGuide Crawling URLS:
FN_SNAPSHOT_URL = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp'
FN_STATEMENT_URL = 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp'

FN_SNAPSHOT_PARAMS = {
    'pGB': '1', 'gicode': '', 'cID': '', 'MenuYn': 'Y', 'ReportGB': '', 'NewMenuID': '11', 'stkGb': '701'
}

FN_STATEMENT_PARAMS = {
    'pGB': '1', 'gicode': '', 'cID': '', 'MenuYn': 'Y', 'ReportGB': 'D', 'NewMenuID': '11', 'stkGb': '701'
}

# 한국거래소 주식 종목코드
KRX_CORP_LIST_URL = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download'

# 수집한 파일을 저장할 NAS 경로
FNGUIDE_FILE_STORAGE_PATH = r'\\ds920\share\skogkatt\fnguide'
FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH = rf'{FNGUIDE_FILE_STORAGE_PATH}\snapshot'
FNGUIDE_STATEMENT_FILE_STORAGE_PATH = rf'{FNGUIDE_FILE_STORAGE_PATH}\statement'

FNGUIDE_STATEMENT_FILE_PREFIX = 'fn_statement_'
FNGUIDE_SNAPSHOT_FILE_PREFIX = 'fn_snapshot_'
