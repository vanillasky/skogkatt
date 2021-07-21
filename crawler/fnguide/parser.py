import re
from collections import OrderedDict
from pathlib import Path
from typing import List

import bs4
import numpy as np
import pandas as pd
from pandas import DataFrame

from skogkatt.conf.crawl_conf import (
    FNGUIDE_SNAPSHOT_FILE_PREFIX, FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH,
    FNGUIDE_STATEMENT_FILE_PREFIX, FNGUIDE_STATEMENT_FILE_STORAGE_PATH
)
from skogkatt.crawler.fnguide.index import FN_HIGHLIGHT_ROW_INDEX, SectorIndexer
from skogkatt.crawler.util import read_from, remove_tag, remove_style, to_dataframe
from skogkatt.errors import StatementParseError
from skogkatt.core.financial.constants import ReportCode, StatementType
from skogkatt.core.financial.dto import FinancialStatementDTO
from skogkatt.core.financial import Statement
from skogkatt.core.financial import StockSummary
from skogkatt.core.financial.synonym import is_synonym, find_synonyms, find_unity_synonym
from skogkatt.core import LoggerFactory
from skogkatt.core.ticker.store import ticker_store

logger = LoggerFactory.get_logger(__name__)


def prepare_statements(stock_code: str, dates: List[str], report_code: int):
    """
    입력받은 날짜(년/월) 개수 만큼 Statement 객체를 만들어 리스트로 반환
    연간/분기 구분이 "연간"인 때에는 12월 자료만 처리하므로
    4개년도 날짜가 넘어와도 생성되는 Statement 개수는 3개가 된다.
    :param stock_code: 종목코드
    :param dates: list contains dates such as ['2020/03', '2020/06', ...]
    :param report_code: 연간/분기 보고서 구분
    :return:
        list contains Statement objects
    """
    statements = []
    for date in dates:
        year = int(date.split('/')[0])
        regex = re.compile('\\([E,P]\\)')
        match = re.search(regex, date.split('/')[1])
        consensus = 0
        if match is None:
            month = date.split('/')[1]
        else:
            month = re.sub(regex, '', date.split('/')[1])
            consensus = 1 if 'E' in match.group() else 2

        if report_code == ReportCode.annual or report_code == ReportCode.summary_annual:
            if int(month) != 12:
                continue

        statement = Statement.create(stock_code, fiscal_date=f'{year}/{month}', consensus=consensus)
        statements.append(statement)

    return statements


class FnSnapshotParser:

    def __init__(self):
        self._soup = None

    @staticmethod
    def resolve_file_path(stock_code):
        file_name = f'{FNGUIDE_SNAPSHOT_FILE_PREFIX}{stock_code}.html'
        file_path = Path(FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH).joinpath(file_name)
        return file_path

    def parse(self, stock_code, file=None) -> FinancialStatementDTO:
        """
        FnGuide 스냅샷 html에서 발행주식수, 연간, 분기 재무제표 자료를 추출한다.
        :param stock_code: str, 주식 종목코드
        :param file: str, optional, 파싱할 파일을 직접 지정하는 경우 파일명
        :return:
            FinancialStatementDTO
        """
        file = self.resolve_file_path(stock_code) if file is None else file
        self._soup = read_from(file)
        tables = self._soup.find_all("table")

        dto = None

        try:
            error_labels = self.validate_labels(tables)
            if len(error_labels) > 0:
                raise StatementParseError(err_msg=f'fnguide label mismatched: {",".join(error_labels)}', stock_code=stock_code)

            summary_tables = self.find_tables_by_caption("Financial Highlight")
            remove_tag(summary_tables[1], "span", "csize")      # 연결 - 연간
            remove_tag(summary_tables[2], "span", "csize")      # 연결 - 분기
            # remove_tag(summary_tables[5], "span", "csize")      # 개별 - 분기

            annual_df = pd.read_html(str(summary_tables[1]), header=1)[0]
            quarter_df = pd.read_html(str(summary_tables[2]), header=1)[0]
            # quarter_ofs_df = pd.read_html(str(summary_tables[5]), header=1)[0]

            dto = FinancialStatementDTO(stock_code)
            dto.stock_summary = self.parse_summary(stock_code, tables)
            dto.annual_abbreviations = self.parse_highlight(stock_code, annual_df, ReportCode.summary_annual)
            dto.quarter_abbreviations = self.parse_highlight(stock_code, quarter_df, ReportCode.summary_quarter)
            # dto.quarter_statements += self.parse_highlight(quarter_ofs_df, ReportCode.summary_quarter, fs_div='OFS')
        except FileNotFoundError as err:
            raise
        except (KeyError, IndexError, ValueError, StatementParseError) as err:
            # logger.error("fnguide snapshot crawl failed - stock_code: %s", stock_code, exc_info=True)
            raise StatementParseError(err_msg=f'fnguide snapshot parse failed - {str(err)}', stock_code=stock_code)

        return dto

    def find_tables_by_caption(self, caption_value: str):
        tables = []
        for caption in self._soup.find_all('caption'):
            if caption.get_text() == caption_value:
                tables.append(caption.find_parent('table'))

        return tables

    @staticmethod
    def validate_labels(tables: List[bs4.element.Tag]):
        """
        추출하고자하는 주식 정보 항목이 일치하는지 확인한다.
        :param tables: List[bs4.element.Tag]
        :return:
            불일치 항목 리스트
        """
        error_labels = []
        labels = dict()

        labels['발행주식수'] = tables[0].select("tr:nth-of-type(7) th:nth-of-type(1) div")[0].get_text().replace('\xa0', ' ').strip()
        labels['자기주식'] = tables[4].select("tr:nth-of-type(5) th:nth-of-type(1) div")[0].get_text().replace('\xa0', ' ').strip()

        for expected, actual in labels.items():
            try:
                assert (actual.startswith(expected))
            except AssertionError as err:
                if not is_synonym(expected, actual):
                    error_labels.append(f'expected: {expected}, actual: {actual}')

        return error_labels

    def parse_summary(self, stock_code: str, tables: List[bs4.element.Tag]) -> StockSummary:
        """
        주식 기본 정보 추출:
        발행 주식수, 우선주, 자기주식 등
        :return:
            StockSummary
        """
        stock_summary = StockSummary(stock_code)

        # 시세현활 [년/월/일] -> 년-월-일
        ref_date = self._soup.find('div', {'id': 'div1'}) \
            .find('span', {'class': 'date'}) \
            .get_text() \
            .replace('[', '').replace(']', '')
        stock_summary.reference_date = ref_date.replace('/', '-')

        # 발행주식수 보통주/우선주
        stock_cnt = tables[0].select("tr:nth-of-type(7) td:nth-of-type(1)")[0].get_text().split('/')

        # 보퉁주식수
        common_stock_cnt = stock_cnt[0].replace(',', '')
        # 우선주식수
        pref_stock_cnt = stock_cnt[1].replace(',', '')

        # 자기주식 from table 주주구분현황
        treasury_stock_cnt = tables[4].select("tr:nth-of-type(5) td:nth-of-type(2)")[0].get_text().strip()
        treasury_stock_cnt = treasury_stock_cnt.replace(',', '')

        stock_summary.common_stock_cnt = int(common_stock_cnt)
        stock_summary.pref_stock_cnt = int(pref_stock_cnt) if len(pref_stock_cnt) > 0 else 0
        stock_summary.treasury_stock_cnt = int(treasury_stock_cnt) if len(treasury_stock_cnt) > 0 else 0

        return stock_summary

    def parse_highlight(self,
                        stock_code: str,
                        fs_df: DataFrame,
                        report_code: int,
                        fs_div: str = 'CFS') -> List[Statement]:
        """
        FnGuide의 Financial Highlight 자료에서 데이터 추출해서 Statement 리스트를 반환

        :param stock_code: 종목코드
        :param fs_df: DataFrame, FnGuide Financial Highlight 테이블
        :param report_code: 연간/분기 구분
        :param fs_div: 연결/별도 재무제표 구분
        :return:
            A List of Statement
        """
        self.validate_index(fs_df)

        fs_df = fs_df.rename(columns={fs_df.columns[0]: 'account_id'})
        """ 첫번째 행인 매출액 필드명이 업종별로 다를 수 있므로 매출액으로 통일한다 """
        if fs_df.loc[0, 'account_id'] != '매출액':
            fs_df.loc[0, 'account_id'] = '매출액'

        """ 요악자료에서 날짜 추출.  """
        dates = fs_df.columns[1:].tolist()

        # """ 분기 자료는 컨센서스 저장안함 """
        # if report_code == ReportCode.summary_quarter:
        #     dates = fs_df.columns[1:6]

        """ 년/월별 재무제표 객체 준비 """
        statements = prepare_statements(stock_code, dates, report_code)

        accounts = fs_df['account_id'].tolist()
        for i in range(len(statements)):
            values = fs_df[fs_df.columns[i + 1]].tolist()
            statements[i].report_code = report_code
            statements[i].fs_div = fs_div
            statements[i].append_facts(accounts, values, None, None, None)

        return statements

    @staticmethod
    def validate_index(fs_df: DataFrame, row_index_dict: dict = None):
        """
        사용중인 행번호 색인의 계정과 FnGuide의 자료가 일치하는지 확인
        :param fs_df: DataFrame, 요약 재무제표
        :param row_index_dict: optional, dict, 행번호 색인
        :return:
            str, 색인 불일치 항목
        """
        if row_index_dict is None:
            row_index_dict = FN_HIGHLIGHT_ROW_INDEX

        fs_df = fs_df.rename(columns={fs_df.columns[0]: 'account_id'})
        account_ids = fs_df['account_id'].tolist()

        legacy_account_ids = row_index_dict.keys()
        if len(legacy_account_ids) != len(account_ids):
            raise StatementParseError(err_msg=f'Account counts are different, legacy: {len(legacy_account_ids)}, parsed: {len(account_ids)}')

        """ 첫번째 행인 매출액 필드명이 업종별로 다를 수 있므로 첫행은 삭제 후 비교 """
        """ 보험업: 보험료수익, 증권업: 순영업수익 등"""
        df_legacy = DataFrame(row_index_dict.items(), columns=['account', 'row_index'])
        df_legacy = df_legacy.drop(df_legacy.index[0])

        df_new = DataFrame()
        df_new['account'] = fs_df['account_id']
        df_new['row_index'] = fs_df.index
        df_new = df_new.drop(df_new.index[0])

        df_legacy['account_match'] = np.where(df_legacy['account'] == df_new['account'], 'True', 'False')
        result = df_legacy.groupby(['account_match']).groups
        invalid_account_rows = result.get('False', None)

        if invalid_account_rows is not None:
            legacy_account_ids = df_legacy.loc[invalid_account_rows]['account'].tolist()
            legacy_row_ids = df_legacy.loc[invalid_account_rows]['row_index'].tolist()
            parsed_account_ids = df_new.loc[invalid_account_rows]['account'].tolist()

            message = (
                f'Mismatched - row_index: {legacy_row_ids}, '
                f'legacy: {legacy_account_ids}, '
                f'parsed: {parsed_account_ids}'
            )

            raise StatementParseError(err_msg=message)


class FnStatementParser:

    def __init__(self):
        self.sector_indexer = None
        self._soup = None
        self.annual_reports = OrderedDict()
        self.quarter_reports = OrderedDict()

    @staticmethod
    def resolve_file_path(stock_code):
        file_name = f'{FNGUIDE_STATEMENT_FILE_PREFIX}{stock_code}.html'
        file_path = Path(FNGUIDE_STATEMENT_FILE_STORAGE_PATH).joinpath(file_name)
        return file_path

    def parse(self, stock_code, file=None, indexer: SectorIndexer = None) -> FinancialStatementDTO:
        """
        재무제표 데이터를 추출해서 FinancialStatementDTO에 담아 반환한다.
        :param stock_code: str, 종목코드
        :param file: str, optional, 파일명. 파싱할 파일을 직접 지정
        :param indexer: SectorIndexer, optional, FnGuide 행번호 색인
        :return:
            FinancialStatementDTO
        """

        try:
            tables = self._prepare_statement_tables(stock_code, file)

            self.classify_reports(tables)
            self.sector_indexer = indexer if indexer is not None else SectorIndexer()

            dto = FinancialStatementDTO(stock_code)
            dto.annual_statements = self.parse_statements(stock_code, ReportCode.annual, self.annual_reports)
            dto.quarter_statements = self.parse_statements(stock_code, ReportCode.quarter, self.quarter_reports)

            return dto
        except FileNotFoundError:
            raise
        except (KeyError, IndexError, StatementParseError, RuntimeError) as err:
            # logger.error("fnguide statement crawl failed - stock_code: %s", stock_code, exc_info=True)
            ticker = ticker_store.find_by_stock_code(stock_code)
            raise StatementParseError(
                err_msg=f'fnguide statement parse failed - {str(err)}',
                stock_code=stock_code, industry=ticker.industry, corp_name=ticker.name)

    def _prepare_statement_tables(self, stock_code, file=None):
        """
        재무제표 HTML Table에서 불필요한 태그와 CSS를 제거해서 반환한다.
        file 인자가 없으면 종목코드로 해당 HTML 파일을 디스크에서 찾는다
        :param stock_code: 종목코드
        :param file: optional, HTML 파일
        :return:
        """
        file = self.resolve_file_path(stock_code) if file is None else file
        self._soup = read_from(file)
        tables = self._soup.find_all("table")

        self.remove_display_none(tables)
        self.remove_link(tables)

        return tables

    def parse_statements(self,
                         stock_code: str,
                         report_code: int,
                         reports: OrderedDict,
                         fs_div: str = 'CFS') -> List[Statement]:
        """
        재무상태표, 손익계산서, 현금흐름표 3개의 DataFrame을 1개의 재무제표로 만들고
        각 재무제표를 년/월별로 담은 List로 반환한다.
        FnGuide 재무제표 html에는 최근 4개년도 또는 분기 자료를 가지고 있으므로 반환되는 리스트는 4개의 재무제표를 포함

        :param stock_code: 종목코드
        :param report_code: int, 년간/분기 구분
        :param reports: dict, 재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)를 key로 갖는 재무제표 DataFrame
        :param fs_div: str, 연결/별도 재무제표 구분, default: 'CFS'
        :return:
            List[Statement]
        """

        """ 재무상태표에서 날짜 추출.  """
        dates = reports.get(StatementType.BS).columns[1:5].tolist()

        """ 날짜(년/월)수 만큼 재무제표 객체 준비 """
        statements = prepare_statements(stock_code, dates, report_code)

        """ 재무상태표, 손익계산서, 현금흐름표를 섹터별로 구분하여 Statement 객체에 저장"""
        for fs_type, report_df in reports.items():
            mismatched_accounts = self.validate_index(report_df, fs_type)

            if len(mismatched_accounts) > 0:
                raise StatementParseError(err_msg=f'Mismatched account(s) detected: {",".join(mismatched_accounts)}')
                # send_telegram_message(mismatched_accounts)

            self.append_facts_to(statements, report_df, report_code, fs_div, fs_type)

        return statements

    def classify_reports(self, html_tables: List[bs4.element.Tag]):
        """
        HTML에서 재무제표를 연간/분기, 재무제표 종류별로 분류해서
        DataFrame으로 변환 후 dict에 저장한다.
        :param html_tables: 재무제표 html table list
        :return:
        """
        # 재무상태표
        self.annual_reports[StatementType.BS] = self.rename_column(to_dataframe(html_tables[2]))
        self.quarter_reports[StatementType.BS] = self.rename_column(to_dataframe(html_tables[3]))

        # 손익계산서
        self.annual_reports[StatementType.IS] = self.rename_column(to_dataframe(html_tables[0]))
        self.quarter_reports[StatementType.IS] = self.rename_column(to_dataframe(html_tables[1]))

        # 현금흐름표
        self.annual_reports[StatementType.CF] = self.rename_column(to_dataframe(html_tables[4]))
        self.quarter_reports[StatementType.CF] = self.rename_column(to_dataframe(html_tables[5]))

    @staticmethod
    def rename_column(df: DataFrame):
        """
        동의어 사전에 해당 계정과목에 대한 동의어가 있으면
        대표 동의으로 통일한다.
        :param df:
        :return:
        """
        df = df.rename(columns={df.columns[0]: 'account_id'})
        for i in range(df.shape[0]):
            account_id = df.loc[i, 'account_id']
            if find_synonyms(account_id) is not None:
                replace = find_unity_synonym(account_id)
                df.loc[i, 'account_id'] = replace

        return df

    @staticmethod
    def remove_display_none(tables):
        [remove_style(each, "tr") for each in tables]

    @staticmethod
    def remove_link(tables):
        [remove_tag(each, "a") for each in tables]

    def append_facts_to(self,
                        statements: List[Statement],
                        fn_statement_df: DataFrame,
                        report_code: int,
                        fs_div: str,
                        fs_type: str):
        """
        Statement 객에체 계정과목(StatementFact)을 추가한다.
        :param statements: 자료를 저장할 Statement 객체 List
        :param fn_statement_df: 재무제표 DataFrame
        :param report_code: 연간/분기 구분
        :param fs_div: 연결/개밸 재무제표 구분 - 연결: CFS, 개별: OFS
        :param fs_type: 재무제표 종류 - 재무상태표: BS, 손익계산서: IS, 현금흐름표: CF
        :return:
            a List of Statement
        """
        # 재무재표에서 추출할 항목의 행번호를 담고있는 dictionary
        sector_indexes = self.sector_indexer.get_sector_indexes(fs_type)

        for sector_name, sector in sector_indexes.items():
            for group_name, group_attributes in sector.items():
                df_group = fn_statement_df.loc[group_attributes.values()]
                df_group['account_id'] = group_attributes.keys()
                df_group['property'] = group_name
                df_group.fillna(0, inplace=True)

                accounts = df_group['account_id'].tolist()
                for i in range(len(statements)):
                    # 년/월 컬럼별 값
                    column_values = df_group[df_group.columns[i + 1]].tolist()
                    statements[i].report_code = report_code
                    statements[i].fs_div = fs_div
                    statements[i].append_facts(accounts, column_values, group_name, sector_name, fs_type)

        return statements

    def validate_index(self, fn_statement_df: DataFrame, fs_type) -> List[str]:
        """
        사용중인 행번호 색인의 계정과 FnGuide의 자료가 일치하는지 확인
        :return:
            List of 계정명 불일치 항목
        """
        mismatched = []
        sector_indexes = self.sector_indexer.get_sector_indexes(fs_type)
        for sector_name, sector in sector_indexes.items():
            for group_name, group_attributes in sector.items():
                row_indexes = list(group_attributes.values())
                df_legacy = DataFrame(group_attributes.items(), columns=['account', 'row_index'])

                # 중복되는 계정과목명을 없애기 위해 "비유동부채.계약부채"와 같이 구분자를 추가한 과목명을 원래 계정명으로 복구
                df_legacy = df_legacy.assign(account=[x.split(".")[-1] for x in df_legacy['account']])

                try:
                    df_check = self.make_account_index(row_indexes, fn_statement_df)
                except KeyError as err:
                    raise StatementParseError(f'Mismatched row index - group: {group_name}, {str(err)}')

                df_legacy['account_match'] = np.where(df_legacy['account'] == df_check['account'], 'True', 'False')
                result = df_legacy.groupby(['account_match']).groups
                invalid_account_rows = result.get('False', None)

                if invalid_account_rows is not None:
                    legacy_account_ids = df_legacy.loc[invalid_account_rows]['account'].tolist()
                    legacy_row_ids = df_legacy.loc[invalid_account_rows]['row_index'].tolist()
                    crawled_account_ids = df_check.loc[invalid_account_rows]['account'].tolist()

                    message = (
                        f'Mismatched - group: {group_name}, '
                        f'row_index: {legacy_row_ids}, '
                        f'legacy: {legacy_account_ids}, '
                        f'parsed: {crawled_account_ids}'
                    )

                    mismatched.append(message)

        return mismatched

    @staticmethod
    def make_account_index(row_indexes: List[int], target_df: DataFrame):
        """
        DataFrame의 계정과목을 기준 행번호로 정렬해서 반환한다.
        :param row_indexes: 기준 행번호
        :param target_df: 대상 DataFrame
        :return:
            DataFrame
        """
        df_check = DataFrame(columns=['account', 'row_index'])

        for i in range(len(row_indexes)):
            check_account_id = target_df.loc[row_indexes[i]]['account_id']
            df_check.loc[i] = [check_account_id, row_indexes[i]]

        df_check.reset_index(inplace=True)
        return df_check
