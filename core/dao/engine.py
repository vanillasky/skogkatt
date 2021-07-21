from abc import ABCMeta, abstractmethod

import pymongo
import sqlalchemy

from skogkatt.conf.app_conf import app_config, Config
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class DBEngine(metaclass=ABCMeta):
    @abstractmethod
    def get_connection(self):
        raise NotImplementedError

    @abstractmethod
    def connect(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_db(self):
        raise NotImplementedError

    @staticmethod
    def _resolve_db_name(db_name):
        if app_config.current_mode == Config.TEST:
            """ 테스트 모드면 DB는 무조건 UNIT_TEST_DB 속성 사용 """
            db_name = app_config.get('UNIT_TEST_DB')
        else:
            db_name = db_name if db_name is not None else app_config.get('BASE_DB')

        return db_name

    def exists_table(self, *args, **kwargs):
        raise NotImplementedError


class MariaEngine(DBEngine):

    def __init__(self, db_name=None):
        self._db = self._resolve_db_name(db_name)
        self._connection = self.connect(self._db)
        logger.debug(f'MariaEngine created. database: {self._db}, current environment: {app_config.current_mode}')

    def connect(self, db_name):
        url = app_config.get('MARIA_URL')
        return sqlalchemy.create_engine(f'{url}/{db_name}', encoding='utf-8')

    def exists_table(self, table_name):
        sql = "select 1 from information_schema.tables where table_schema = '%s' and table_name = '%s'"
        rows = self._connection.execute(sql % (self._db, table_name)).fetchall()
        return len(rows) > 0

    def get_connection(self):
        return self._connection

    def get_db(self):
        return self._db


class MongoEngine(DBEngine):

    def __init__(self, db_name=None):
        self._connection = self.connect()
        self._connection.server_info()
        db_name = self._resolve_db_name(db_name)
        self._db = self._connection[db_name]
        logger.debug(f'MongoDAO created for database: {db_name}, current environment: {app_config.current_mode}')

    def connect(self):
        url = app_config.get('MONGO_URL')
        return pymongo.MongoClient(url, serverSelectionTimeoutMS=10000)

    def exists_table(self, table_name):
        return True if table_name in self._db.list_collection_names() else False

    def get_connection(self):
        return self._connection

    def get_db(self):
        return self._db
