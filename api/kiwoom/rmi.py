from typing import List


def get_repeat_cnt(api, tr_code, record_name):
    """
    레코드 반복 횟수를 반환한다.
    :param api: API Control - QAxWidget instance
    :param tr_code: Tran 코드
    :param record_name: 레코드명
    :return: 레코드의 반복횟수
    Ex.) GetRepeatCnt(“OPT00001”, “주식기본정보”)
    """
    return api.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, record_name)


def get_comm_data(api, tr_code, record_name, index, item_name):
    """
    수신 데이터를 반환한다.
    :param api: API Control - QAxWidget instance
    :param tr_code: Tran 코드
    :param record_name: 레코드명
    :param index: 복수데이터 인덱스
    :param item_name: 아이템명
    :return: 수신 데이터
    Ex.) 현재가 출력 - GetCommData('OPT00001', '주식기본정보', 0, '현재가')
    """
    return api.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, record_name, index, item_name)


def get_comm_real_data(api, stock_code, fid):
    """
    실시간 시세 데이터를 반환한다.
    :param api: API Control - QAxWidget instance
    :param stock_code: 종목코드
    :param fid: 실시간 ID
    :return: 실시간 시세데이터
    """
    return api.dynamicCall("GetCommRealData(QString, int)", stock_code, fid)


def connect(api):
    """
    로그인 윈도우를 실행한다.
    OnEventConnect 이벤트가 발생하고 이벤트의 인자값으로 성공여부 확인가능
    :param api: API Control - QAxWidget instance
    :return: 0 - 성공, 음수값은 실패
    """
    api.dynamicCall("CommConnect()")


def get_order_sign_data(api, fid):
    """
    체결잔고 데이터를 반환한다.
    :param api: API Control - QAxWidget instance
    :param fid: 체결잔고 아이템. See fid.py
    :return: 수신 데이터
    Ex.)현재가 출력 - GetChejanData(10)
    """
    return api.dynamicCall("GetChejanData(int)", fid)


def get_master_code_name(api, code):
    """
    종목코드의 한글명을 반환한다.
    장내외, 지수선옵, 주식선옵 검색 가능
    :param api: API Control - QAxWidget instance
    :param code: 종목코드
    :return: 종목 한글명
    """
    code_name = api.dynamicCall("GetMasterCodeName(QString)", code)
    return code_name


def get_connect_state(api):
    """
    현재접속상태를 반환한다.
    :param api:
    :return: 0: 미연결, 1: 연결완료
    """
    return api.dynamicCall("GetConnectState()")


def set_input_value(api, prop_id, value):
    """
    Tran 입력값을 서버 통신 전에 입력한다
    Ex) SetInputValue('종목코드', '000660')

    :param api:
    :param prop_id: 아이템명
    :param value: 입력값
    :return: 없음
    """
    api.dynamicCall("SetInputValue(QString, QString)", prop_id, value)


def comm_rq_data(api, rq_name, tr_code, _next, screen_no):
    """
    Tran을 서버로 송신한다.
    Ex) CommRqData( “RQ_1”, “OPT00001”, 0, “0101”)
    :param api:
    :param rq_name: 사용자구분명
    :param tr_code: Tran 코드
    :param _next: 0:조회, 2: 연속
    :param screen_no: 4자리의 화면번호
    :return:
    """
    return api.dynamicCall("CommRqData(QString, QString, int, QString)", rq_name, tr_code, _next, screen_no)


def get_login_info(api, tag):
    return api.dynamicCall("GetLoginInfo(QString)", tag)


def get_master_stock_state(api, ticker):
    """
    종목코드의 상태를 반환한다.
    :param api: kiwoom ocx control
    :param ticker: 종목코드
    :return: 종목상태
    종목상태 – 정상, 증거금100%, 거래정지, 관리종목, 감리종목, 투자유의종목, 담보대출, 액면분할, 신용가능
    """
    return api.dynamicCall("GetMasterStockState(QString)", ticker)


def send_order(api=None, rq_name=None, screen_no=None, acc_no=None, order_type=None,
               code=None, quantity=None, price=None, price_type=None, order_no=""):
    """
    주식 주문 TR 송신
    :param api: QAxWidget object
    :param rq_name: 사용자 구분 요청 명
    :param screen_no: 화면번호[4]
    :param acc_no: 계좌번호[10]
    :param order_type: 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정
    :param code: 주식종목코드
    :param quantity: 주문수량
    :param price: 주문단가
    :param price_type: 거래구분
    :param order_no: 원주문번호
    :return:
    """
    api.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    [rq_name, screen_no, acc_no, order_type, code, quantity, price, price_type, order_no])


def get_server_type(api):
    return api.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")


def set_real_reg(api, screen_no, codes, fids, opt_type):
    """
    실시간 DATA 등록
    opt_type “0”은 항상 마지막에 등록한 종목들만 실시간등록이 됩니다.
    opt_type “1”은 이전에 실시간 등록한 종목들과 함께 실시간을 받고 싶은 종목을 추가로 등록할 때 사용합니다.
    종목, FID는 각각 한번에 실시간 등록 할 수 있는 개수는 100개 입니다.
    :param api: QAXWidget, API Control
    :param screen_no: str, 화면번호
    :param codes: str, 종목코드 리스트(ex: 039490;005930;...)
    :param fids: str, FID 번호(ex:9001;10;13;...). FID 번호는 KOA Studio에서 실시간 목록을 참고
    :param opt_type: str, 타입(“0”, “1”)
    :return:
    """
    return api.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fids, opt_type)


def register_realtime(api, stock_codes: List[str], params: dict):
    """
    See set_real_reg
    :param api:
    :param stock_codes:
    :param params:
    :return:
    """
    str_code = ';'.join(stock_codes)
    return set_real_reg(api, params.get('screen_no'), str_code, params.get('fids'), params.get('opt_type'))


def load_condition(api):
    """
    long GetConditionLoad()
    서버에 저장된 사용자 조건식을 조회해서 임시로 파일에 저장
    System 폴더에 아이디_NewSaveIndex.dat파일로 저장된다. Ocx가 종료되면 삭제시킨다.
    조건검색 사용시 이함수를 최소 한번은 호출해야 조건검색을 할 수 있다.
    영웅문에서 사용자 조건을 수정 및 추가하였을 경우에도 최신의 사용자 조건을 받고 싶으면 다시 조회해야한다
    :param api:
    :return:
    """
    ret = api.dynamicCall("GetConditionLoad()")
    if ret == 0:
        raise RuntimeError("GetConditionLoad() Failed.")


def get_condition_list(api):
    return api.dynamicCall("GetConditionNameList()")


def send_condition(api, screen_no, cond_name, cond_index, search_type):
    """
    조건검색 종목조회 TR 송신한다.

    BOOL SendCondition(LPCTSTR strScrNo, LPCTSTR strConditionName, int nIndex, int nSearch)
    LPCTSTR strScrNo : 화면번호
    LPCTSTR strConditionName : 조건명
    int nIndex : 조건명인덱스
    int nSearch : 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)

    :param api:
    :param screen_no: str, 화면번호
    :param cond_name: str, 조건명
    :param cond_index: str, 조건명 인덱스
    :param search_type: int, 조회구분
    :return:
    """
    return api.dynamicCall("SendCondition(QString, QString, int, int)", screen_no, cond_name, cond_index, search_type)


def stop_send_condition(api, screen_no, cond_name, cond_index):
    """
    조건검색 실시간 중지 TR 전송
    Void SendConditionStop(LPCTSTR strScrNo, LPCTSTR strConditionName, int nIndex)
    :param api:
    :param screen_no: str, 화면번호
    :param cond_name: str, 조건명
    :param cond_index: str, 조건명 인덱스
    :return:
    """
    return api.dynamicCall("SendConditionStop(QString, QString, int, int)", screen_no, cond_name, cond_index)
