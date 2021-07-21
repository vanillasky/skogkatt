from tabulate import tabulate

from skogkatt.conf.app_conf import app_config, Config
from skogkatt.core.ticker.store import ticker_store
from skogkatt.screeners.rim.pricer import Pricer

app_config.set_mode(Config.TEST)


def test_estimate_price():
    stock_code = "192440"
    ticker = ticker_store.find_by_stock_code(stock_code)

    pricer = Pricer()
    estimate = pricer.estimate(ticker)
    print(tabulate(estimate.as_dataframe(), headers="keys", tablefmt="psql", numalign="right"))
    print(f"매수: {estimate.buy_price}, 매도: {estimate.sell_price}, 적정: {estimate.affordable_price}")
    print(estimate.to_dict())

