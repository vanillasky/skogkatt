from pandas import DataFrame


class StatementFact:

    def __init__(self, account_name, value, group, sector, sj_div):
        self.account_name = account_name
        self.value = value
        self.group = group
        self.sector = sector
        self.sj_div = sj_div

    def __str__(self):
        return 'account: {self.account_name}, ' \
               'value: {self.value}, ' \
               'group: {self.group}, ' \
               'sector: {self.sector}, ' \
               'sj_div: {self.sj_div}, ' \
               .format(self=self)


class Statement:

    def __init__(self,
                 stock_code: str,
                 fiscal_date: str,
                 report_code: str = None,
                 consensus: int = 0,
                 fs_div: str = None):

        self.stock_code = stock_code
        self.fiscal_date = fiscal_date
        self.report_code = report_code
        self.consensus = consensus
        self.fs_div = fs_div
        self.facts = []
        self.fact_lookup = {}

    @staticmethod
    def create(stock_code: str,
               fiscal_date: str,
               consensus: int = 0,
               report_code: int = None,
               fs_div: str = None):
        """
        재무제표 자료 생성
        :param stock_code: 종목코드
        :param fiscal_date: 회계일자
        :param consensus: 컨센서트 여부 - 0: 컨센아님, 1: 컨센, 2: 잠정실적
        :param report_code: 보고서 구분, 연간: 1, 분기: 2
        :param fs_div: 재무제표 연결/별도 구분, CFS: 연결: OFS: 별도
        :return:
            Statement object
        """

        statement = Statement(stock_code, fiscal_date, report_code, consensus, fs_div)

        return statement

    def __str__(self):
        facts = [fact.__str__() for fact in self.facts]

        string_value = 'Statement: stock_code: {self.stock_code}, fiscal_date: {self.fiscal_date}, ' \
                       'consensus: {self.consensus}, ' \
                       'report_code: {self.report_code}, ' \
                       'fs_div: {self.fs_div}, ' \
                       .format(self=self)

        return string_value + 'facts[ ' + ','.join(facts) + ']'

    def append_facts(self, accounts, values, group, sector, sj_div):
        """
        계정과목과 값을 추가한다.
        :param accounts: 계정과목 List
        :param values: 값 List
        :param group: 섹터내 자료구분
        :param sector: 섹터명
        :param sj_div: 재무재표 종류 - BS: 재무상태표, IS: 손익계산서, CF: 현금흐름표, SM: FnGuide 요약
        :return:
        """

        for i in range(len(accounts)):
            fact = StatementFact(accounts[i], values[i], group, sector, sj_div)
            self.fact_lookup[accounts[i]] = fact
            self.facts.append(fact)

    def get_fact(self, account_id) -> StatementFact:
        return self.fact_lookup.get(account_id, None)

    def to_dataframe(self):
        df = DataFrame()
        df['account_id'] = [fact.account_name for fact in self.facts]
        df['stock_code'] = self.stock_code
        df['fiscal_date'] = self.fiscal_date

        df = df[['stock_code', 'fiscal_date', 'account_id']]
        df['value'] = [fact.value for fact in self.facts]
        df['attribute'] = [fact.group for fact in self.facts]
        df['sector'] = [fact.sector for fact in self.facts]
        df['report_code'] = self.report_code
        df['fs_div'] = self.fs_div
        df['sj_div'] = [fact.sj_div for fact in self.facts]
        df['consensus'] = self.consensus

        return df

    def from_dataframe(self):
        pass


class StockSummary:

    def __init__(self, stock_code):
        self.stock_code = stock_code
        self.reference_date = None
        self.common_stock_cnt = 0
        self.pref_stock_cnt = 0
        self.treasury_stock_cnt = 0

    def __str__(self):
        string_value = 'StockSummary [stock_code:' + self.stock_code \
            + ', reference_date: ' + str(self.reference_date) \
            + ', common_stock_cnt: ' + str(self.common_stock_cnt) \
            + ', pref_stock_cnt: ' + str(self.pref_stock_cnt) \
            + ', treasury_stock_cnt: ' + str(self.treasury_stock_cnt) \
            + ']'

        return string_value

    def to_dict(self):
        return {'stock_code': self.stock_code,
                'reference_date': self.reference_date,
                'common_stock_cnt': self.common_stock_cnt,
                'pref_stock_cnt': self.pref_stock_cnt,
                'treasury_stock_cnt': self.treasury_stock_cnt}

    @staticmethod
    def from_dict(dic_data: dict):
        summary = StockSummary(dic_data.get('stock_code'))
        summary.common_stock_cnt = dic_data.get('common_stock_cnt')
        summary.pref_stock_cnt = dic_data.get('pref_stock_cnt')
        summary.treasury_stock_cnt = dic_data.get('treasury_stock_cnt')
        summary.reference_date = dic_data.get('reference_date')

        return summary
