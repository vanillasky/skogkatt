import pymongo
import sqlalchemy
from pandas import DataFrame
from tabulate import tabulate

from skogkatt.conf.app_conf import app_config
from skogkatt.core import LoggerFactory
from skogkatt.core.dao.engine import DBEngine, MariaEngine, MongoEngine

logger = LoggerFactory.get_logger(__name__)


def copy_tickers_to(target_engine: DBEngine, source: DataFrame = None):
    """ 종목코드를 대상 데이터베이스에 복사한다. """
    conn = target_engine.get_connection()

    if source is not None:
        source['code'] = source['code'].map('{:06d}'.format)
        source['name'] = source['name'].str.strip()

        if isinstance(target_engine, MariaEngine):
            source.to_sql(name="ticker", con=conn, if_exists='replace', index=False)

        elif isinstance(target_engine, MongoEngine):
            target_engine.get_db()['ticker'].insert_many(source.to_dict(orient="records"))
    else:
        tickers = get_tickers()

        if isinstance(target_engine, MariaEngine):
            df = DataFrame(tickers)
            # print(tabulate(df, headers="keys", tablefmt="psql"))
            df.to_sql(name="ticker", con=conn, if_exists='replace', index=False)
        elif isinstance(target_engine, MongoEngine):
            target_engine.get_db()['ticker'].insert_many(tickers)


def get_tickers():
    url = app_config.get('MONGO_URL')
    engine = pymongo.MongoClient(url, serverSelectionTimeoutMS=10000)
    engine.server_info()
    source_db = engine['skogkatt']

    source_tickers = source_db['ticker'].find({}, {'_id': 0})

    return source_tickers


def copy_tickers_to_maria():
    tickers = get_tickers()
    url = app_config.get('MARIA_URL')
    conn = sqlalchemy.create_engine(f'{url}/skogkatt_unit_test', encoding='utf-8')
    df = DataFrame(tickers)
    # print(tabulate(df, headers="keys", tablefmt="psql"))
    df.to_sql(name="ticker", con=conn, if_exists='replace', index=False)


if '__main__' == __name__:
    pass
    # copy_tickers(app_config.get('UNIT_TEST_DB'))
    # copy_tickers_to_maria()

