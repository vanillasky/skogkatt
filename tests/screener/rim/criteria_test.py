import pytest
from pandas import DataFrame
from tabulate import tabulate

from skogkatt.screeners.rim import Criteria


@pytest.fixture
def roe_estimate(request):
    sample_data = {'2018/12': {'영업자산이익률': None, '비영업자산이익률': None, '차입이자율': None, 'ROE': 19.63},
                   '2019/12': {'영업자산이익률': 12.4, '비영업자산이익률': 2.75, '차입이자율': 4.03, 'ROE': 19.63},
                   '2020/12': {'영업자산이익률': 12.37, '비영업자산이익률': 2.76, '차입이자율': 4.15, 'ROE': 8.69},
                   '최근4분기(2020/09)': {'영업자산이익률': 15.61, '비영업자산이익률': 0.68, '차입이자율': 3.25, 'ROE': 9.92},
                   '가중평균': {'영업자산이익률': 18.61, '비영업자산이익률': 1.20, '차입이자율': 3.44, 'ROE': 12.34}}

    df = DataFrame.from_dict(sample_data)
    selected = 'applied_value'
    yield df, selected

    return df


def test_apply_criteria(roe_estimate):
    """
    ROE 추정 조건 적용 테스트
    ROE 추정시 계산 조건 적용시 지정된 조건(가중평균 또는 최근)에 해당하는 값으로
    DataFrame이 만들어 지는지 확인
    """
    df, selected = roe_estimate
    # print(tabulate(df, headers="keys", tablefmt="psql", numalign="right"))

    criteria = Criteria(default_option='가중평균')
    result_df = criteria.apply(df)
    # print(tabulate(result_df, headers="keys", tablefmt="psql", numalign="right"))
    assert (result_df.loc['영업자산이익률', selected] == df.loc['영업자산이익률', '가중평균'])
    assert (result_df.loc['비영업자산이익률', selected] == df.loc['비영업자산이익률', '가중평균'])
    assert (result_df.loc['차입이자율', selected] == df.loc['차입이자율', '가중평균'])

    criteria = Criteria(default_option='최근')
    result_df = criteria.apply(df)

    # print(tabulate(result_df, headers="keys", tablefmt="psql", numalign="right"))
    filter_col = [col for col in df if col.startswith('최근')][0]
    assert (result_df.loc['영업자산이익률', selected] == df.loc['영업자산이익률', filter_col])
    assert (result_df.loc['비영업자산이익률', selected] == df.loc['비영업자산이익률', filter_col])
    assert (result_df.loc['차입이자율', selected] == df.loc['차입이자율', filter_col])



