"""
FnGuide HTML을 DataFrame으로 변환시 참조할 행번호.
"""
from collections import OrderedDict

from skogkatt.core.financial.constants import StatementType, StatementSector

""" FnGuide Financial Highlight Table """
FN_HIGHLIGHT_ROW_INDEX = {
    '매출액': 0,
    '영업이익': 1,
    '영업이익(발표기준)': 2,
    '당기순이익': 3,
    '지배주주순이익': 4,
    '비지배주주순이익': 5,
    '자산총계': 6,
    '부채총계': 7,
    '자본총계': 8,
    '지배주주지분': 9,
    '비지배주주지분': 10,
    '자본금': 11,
    '부채비율': 12,
    '유보율': 13,
    '영업이익률': 14,
    '지배주주순이익률': 15,
    'ROA': 16,
    'ROE': 17,
    'EPS': 18,
    'BPS': 19,
    'DPS': 20,
    'PER': 21,
    'PBR': 22,
    '발행주식수': 23,
    '배당수익률': 24
}

""" --------------- 자금조달 분석 자료 ----------------"""
# 신용조달(재무상태표)
CREDIT_FINANCING = {
    '매입채무및기타유동채무': 34,
    '유동종업원급여충당부채': 35,
    '기타단기충당부채': 36,
    '당기법인세부채': 37,
    '계약부채': 38,
    '반품(환불)부채': 39,
    '배출부채': 40,
    '기타유동부채': 41,
    '장기매입채무및기타비유동채무': 47,
    '비유동종업원급여충당부채': 48,
    '기타장기충당부채': 49,
    '이연법인세부채': 50,
    '장기당기법인세부채': 51,
    '비유동부채.계약부채': 52,
    '비유동부채.반품(환불)부채': 53,
    '비유동부채.배출부채': 54,
    '기타비유동부채': 55
}

# 외부차입(재무상태표)
EXTERNAL_BORROWING = {
    '단기사채': 30,
    '단기차입금': 31,
    '유동성장기부채': 32,
    '유동금융부채': 33,
    '사채': 44,
    '장기차입금': 45,
    '비유동금융부채': 46
}

# 유보이익(재무상태표)
RETAINED_PROFIT = {'기타포괄손익누계액': 63, '이익잉여금(결손금)': 64}

# 주주투자(재무상태표)
HOLDER_INVESTMENT = {'자본금': 59, '신종자본증권': 60, '자본잉여금': 61, '기타자본': 62}

# 지배주주지분(재무상태표)
HOLDER_EQUITY = {'지배주주지분': 58}

# 비지배주주지분(재무상태표)
NC_HOLDER_EQUITY = {'비지배주주지분': 65}

# 기타(재무상태표)
FINANCING_ETC = {'매각예정으로분류된처분자산집단에포함된부채': 42, '기타금융업부채': 56}

""" --------------- 자산투자 분석 자료 ----------------"""

# 설비투자(재무상태표)
EQUIPMENT_INVESTMENT = {'유형자산': 14, '무형자산': 15, '비유동생물자산': 16}

# 운전자산
OPERATING_ASSET = {'재고자산': 2, '유동생물자산': 3,  '매출채권및기타유동채권': 5,
                   '당기법인세자산': 6,  '유동.계약자산': 7,  '유동.반품(환불)자산': 8,
                   '유동.배출권': 9,  '기타유동자산': 10,  '장기매출채권및기타비유동채권': 20,
                   '이연법인세자산': 21,  '장기당기법인세자산': 22,  '계약자산': 23,
                   '비유동.반품(환불)자산': 24,  '비유동.배출권': 25,  '기타비유동자산': 26}

# 금융투자
FINANCIAL_INVESTMENT = {'투자부동산': 17,  '장기금융자산': 18,  '관계기업등지분관련투자자산': 19}

# 여유자금
EXTRA_FUND = {'현금및현금성자산': 11, '유동금융자산': 4}

# 자산투자 - 기타
INVESTMENT_ETC = {'매각예정비유동자산및처분자산집단': 12, '기타금융업자산': 27}

""" --------------- 손익자료 ----------------"""
# 손익자료(손익계산서)
INCOME_STATEMENT = {
    '영업이익': 12, '이자비용': 27, '법인세비용': 73, '당기순이익': 76, '지배주주순이익': 77, '비지배주주순이익': 78
}

""" --------------- 현금흐름 자료 ----------------"""
CASH_FLOW = {'영업활동으로인한현금흐름': 0, '이자지급(-)': 77, '투자활동으로인한현금흐름': 83, '재무활동으로인한현금흐름': 120}


STATEMENT_SECTORS = {
    'income': OrderedDict({
        '영업이익': {'영업이익': INCOME_STATEMENT.get('영업이익')},
        '이자비용': {'이자비용': INCOME_STATEMENT.get('이자비용')},
        '법인세비용': {'법인세비용': INCOME_STATEMENT.get('법인세비용')},
        '당기순이익': {'당기순이익': INCOME_STATEMENT.get('당기순이익')},
        '지배주주순이익': {'지배주주순이익': INCOME_STATEMENT.get('지배주주순이익')},
        '비지배주주순이익': {'비지배주주순이익': INCOME_STATEMENT.get('비지배주주순이익')},
    }),
    'cash_flow': OrderedDict({
        '영업활동으로인한현금흐름': {'영업활동으로인한현금흐름': CASH_FLOW.get('영업활동으로인한현금흐름')},
        '이자지급(-)': {'이자지급(-)': CASH_FLOW.get('이자지급(-)')},
        '투자활동으로인한현금흐름': {'투자활동으로인한현금흐름': CASH_FLOW.get('투자활동으로인한현금흐름')},
        '재무활동으로인한현금흐름': {'재무활동으로인한현금흐름': CASH_FLOW.get('재무활동으로인한현금흐름')},
    }),
    'financing': OrderedDict({
        '신용조달': CREDIT_FINANCING,
        '외부차입': EXTERNAL_BORROWING,
        '유보이익': RETAINED_PROFIT,
        '주주투자': HOLDER_INVESTMENT,
        '지배주주지분': HOLDER_EQUITY,
        '비지배주주지분': NC_HOLDER_EQUITY,
        '기타': FINANCING_ETC
    }),
    'investment': OrderedDict({
        '설비투자': EQUIPMENT_INVESTMENT,
        '운전자산': OPERATING_ASSET,
        '금융투자': FINANCIAL_INVESTMENT,
        '여유자금': EXTRA_FUND,
        '기타': INVESTMENT_ETC
    })
}


class SectorIndexer:
    """
    FnGuide 재무제표에서 필요한 자료를 섹터별로 나누어서 저장하기 위한 행번호 색인.
    섹터는 아래와 같이 4개로 구분하고:
    자금조달(financing), 자산투자(investment), 손익자료(income), 현금흐름(cash_flow)

    각 섹터는 그룹으로 구분하여 계정과목을 그룹으로 분류해서 저장하기 위함.
    ex) 자금조달 섹터: 신용조달 그룹[계약부채, 배출부채, ...]
                     외부차입 그룹[단기사채, 단기차입금, ...]

    """
    __slots__ = ('financing', 'investment', 'income', 'cash_flow', 'statement_sectors')

    def __init__(self, statement_sectors: dict = None):
        if statement_sectors is None:
            statement_sectors = STATEMENT_SECTORS

        super(SectorIndexer, self).__setattr__('financing', statement_sectors.get('financing'))
        super(SectorIndexer, self).__setattr__('investment', statement_sectors.get('investment'))
        super(SectorIndexer, self).__setattr__('income', statement_sectors.get('income'))
        super(SectorIndexer, self).__setattr__('cash_flow', statement_sectors.get('cash_flow'))
        super(SectorIndexer, self).__setattr__('statement_sectors', statement_sectors)

    def find(self, name: str):
        if name == StatementSector.financing:
            return self.financing
        elif name == StatementSector.investment:
            return self.investment
        elif name == StatementSector.income:
            return self.income
        elif name == StatementSector.cash_flow:
            return self.cash_flow
        else:
            raise ValueError(f'Unknown sector name: {name}')

    def get_sector_indexes(self, fs_type: str) -> OrderedDict:
        """
        재무제표 종류별 행번호를 담고있는 dictionary를 찾아서 반환
        :param fs_type: str, 재무제표 종류: BS, IS, CF
        :return:
        """
        sectors = OrderedDict()
        if fs_type == StatementType.BS:
            sectors[StatementSector.financing] = self.financing
            sectors[StatementSector.investment] = self.investment
        elif fs_type == StatementType.IS:
            sectors[StatementSector.income] = self.income
        elif fs_type == StatementType.CF:
            sectors[StatementSector.cash_flow] = self.cash_flow
        else:
            raise ValueError(f'Unknown report class name: {fs_type}')

        return sectors

    def __setattr__(self, *args):
        raise TypeError('SectorIndexer cannot be modified')

    def __delattr__(self, *args):
        raise TypeError('SectorIndexer properties cannot be deleted')

    def __str__(self):
        string_value = (
            f'financing: {self.financing}\n'
            f'investment: {self.investment}\n'
            f'income: {self.income}\n'
            f'cash_flow: {self.cash_flow}\n'
        )
        return string_value
