from skogkatt.core.ticker import Ticker
from skogkatt.core.ticker.store import ticker_store


# def test_save_file():
#     ticker_store.save_file()


def test_find_ticker():
    ticker: Ticker = ticker_store.find_by_name("삼성전자")[0]

    assert ("삼성전자" == ticker_store.find_by_stock_code("005930").name)
    assert ("005930" == ticker_store.find_by_name("삼성전자")[0].code)
    assert (ticker.corp_code == ticker_store.find_by_corp_code(ticker.corp_code).corp_code)
