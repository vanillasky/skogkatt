from skogkatt.core.dao import dao_factory
from skogkatt.core.dao.idao import TickerDAO
from skogkatt.core.dao.maria.ticker import MariaTickerDAO
from skogkatt.core.dao.mongo.ticker import MongoTickerDAO


def test_get_dao():

    ticker_dao = dao_factory.get('TickerDAO')
    assert (isinstance(ticker_dao, TickerDAO))
    # assert (isinstance(ticker_dao, MongoTickerDAO))


def test_register_dao():
    dao_factory.register_dao('TickerDAO', MariaTickerDAO())
    dao = dao_factory.get('TickerDAO')
    assert (isinstance(dao, MariaTickerDAO))
