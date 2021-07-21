import pymongo
import pytest
import sqlalchemy

from skogkatt.conf.app_conf import app_config, Config
from skogkatt.core import LoggerFactory


class DBConf:
    def cleanup(self):
        pass

    def exists_table(self, table_name):
        pass

    def get_logger_name(self):
        pass


class MariaConf(DBConf):
    def __init__(self, config):
        self.db = config["handlers"]["mariadb"]["db"]
        self.host = config["handlers"]["mariadb"]["host"]
        self.table = config["handlers"]["mariadb"]["table"]
        self.conn = sqlalchemy.create_engine(f'{self.host}/{self.db}', encoding='utf-8')

    def cleanup(self):
        if self.exists_table(self.table):
            self.conn.execute(f"drop table {self.table}")

    def exists_table(self, table_name):
        sql = "select 1 from information_schema.tables where table_schema = '%s' and table_name = '%s'"
        rows = self.conn.execute(sql % (self.db, table_name)).fetchall()
        return len(rows) > 0

    def get_logger_name(self):
        sql = f"select * from {self.table}"
        return self.conn.execute(sql).fetchall()[0][5]


class MongoConf(DBConf):
    def __init__(self, config):
        self.db = config["handlers"]["mongodb"]["db"]
        self.host = config["handlers"]["mongodb"]["host"]
        self.table = config["handlers"]["mongodb"]["collection"]
        self.conn = pymongo.MongoClient(self.host)

    def cleanup(self):
        if self.exists_table(self.table):
            self.conn[self.db].drop_collection(self.table)

    def exists_table(self, table_name):
        if table_name in self.conn[self.db].list_collection_names():
            return True
        return False

    def get_logger_name(self):
        return list(self.conn[self.db][self.table].find())[0].get("logger_name")


TEST_LOGGER_NAME = 'queue_log_test'


@pytest.fixture
def handle_log_result(request):
    app_config.set_mode(Config.TEST)

    logger = LoggerFactory.get_logger(TEST_LOGGER_NAME)
    config = LoggerFactory.get_config()
    logger.debug("Debug log message")
    logger.info("Info log message")
    logger.warning("Warning log message")

    try:
        1 / 0
    except ZeroDivisionError as err:
        logger.error('test zero division', exc_info=True)

    db_conf: DBConf = None
    if "maria" == request.param:
        db_conf = MariaConf(config)
    elif "mongo" == request.param:
        db_conf = MongoConf(config)

    def teardown():
        db_conf.cleanup()

    request.addfinalizer(teardown)

    return db_conf


@pytest.mark.parametrize('handle_log_result', ['mongo', 'maria'], indirect=['handle_log_result'])
def test_handler(handle_log_result):
    """
    conf/logging_conf.yaml 참조.
    테스트용 로거 'queue_log_test'는 핸들러 console, tr_file, mongodb, mariadb를 사용한다.
    로깅시 큐를 사용하기 위해 각각의 핸들러는 'QueueListenerHandler' 에 등록된다.

    이 테스트틀 통해 QueueListenerHandler, MongoLogHandler, MariaLogHandler 기능을 확인한다.

    :param handle_log_result:
    :return:
    """
    db: DBConf = handle_log_result
    logger_name = db.get_logger_name()
    assert (TEST_LOGGER_NAME == logger_name)



