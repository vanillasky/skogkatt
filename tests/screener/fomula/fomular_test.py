from tabulate import tabulate

from skogkatt.api.ebest.broker import EBestBroker
from skogkatt.core.dao import dao_factory
from skogkatt.screeners.formula import FormulaScreener


def test_formula():
    screener = FormulaScreener(EBestBroker())
    screener.start(crawl=False)
    dao = dao_factory.get("FormulaScreenerDAO")
    df = dao.find()
    print(tabulate(df, headers="keys", tablefmt="psql"))
