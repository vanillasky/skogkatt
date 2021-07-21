# 연속조회 키움 API 참조. 2: 연속조회 있음, 0: 연속조회 없음
NEXT = 2

MAX_API_CALL = 400

TR_REQ_TIME_INTERVAL = 0.3

# 일봉 수집 시 종목별 수집 간격(초)
CHART_TR_TIME_INTERVAL = 3

# 예수금상세현황요청
TR_RETRIEVE_DEPOSIT = {'rq_name': 'opw00001_req', 'tr_code': 'opw00001', 'tr_name': '예수금상세현황요청', 'next': 0, 'screen_no': '2000'}

# 계좌평가잔고내역요청
TR_ACCOUNT_BALANCE = {'rq_name': 'opw00018_req', 'tr_code': 'opw00018', 'tr_name': '계좌평가잔고내역요청', 'next': 0, 'screen_no': '2002'}

# 주문 전송
TR_SEND_ORDER = {'rq_name': 'send_order_req', 'screen_no': '0101'}

# 일봉 데이터 조회
TR_DAILY_STOCK_CHART = {'rq_name': 'opt10081_req', 'tr_code': 'opt10081', 'tr_name': '주식일봉차트조회요청', 'screen_no': '2001'}

# 조건검색 조회
TR_CONDITIONAL_SEARCH = {'rq_name': 'cond_search', 'tr_code': 'cond_search', 'tr_name': '조건검색요청', 'screen_no': '2003'}

# 실시간 데이터 조회
RT_CURRENT_PRICE = {'screen_no': '3001', 'fids': '9001;10', 'opt_type': '1'}

# 실시간 데이터 조회 끝


# 조건검색 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
COND_SEARCH_CONT = 2
COND_SEARCH_DEFAULT = 0
COND_SEARCH_REAL = 1

FID_ORDER_NO = 9203  # 주문번호
FID_ITEM_NAME = 302  # 종목명
FID_ORDER_QTY = 900  # 주문수량
FID_ORDER_PRICE = 901  # 주문가격
FID_UNDECIDED = 902  # 미체결 수량
FID_SRC_ORDER_NO = 904  # 원주문번호
FID_ORDER_TYPE = 905  # 주문구분
FID_SETTLEMENT_TIME = 908  # 주문체결 시각
FID_SETTLEMENT_NO = 909  # 체결번호
FID_SETTLEMENT_PRICE = 910  # 체결가
FID_SETTLEMENT_QTY = 911  # 체결수량


# OP_ERR_SISE_OVERFLOW = -200    # 과도한 시세조회로 인한 통신불가
# OP_ERR_RQ_STRUCT_FAIL = -201   # 전문 작성 초기화 실패
# OP_ERR_RQ_STRING_FAIL = -202   # 요청전문 작성 실패
# OP_ERR_NONE = 0                # 정상처리

ORDER_TYPES = {'매수': 1, '매도': 2, '매수취소': 3, '매도취소': 4, '매수정정': 5, '매도정정': 6}
PRICE_TYPES = {'지정가': "00", '시장가': "03"}

###################################################
#  SetInputValue 호출시 사용하는 파라미터
###################################################
PARAM_ACCOUNT_NO = "계좌번호"
PARAM_ITEM_CODE = "종목코드"
PARAM_BASE_DATE = "기준일자"
PARAM_MOD_PRICE_TYPE = "수정주가구분"