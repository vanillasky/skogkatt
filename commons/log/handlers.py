import atexit
import logging


from datetime import datetime
from logging.config import valid_ident
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from bson import InvalidDocument
from pandas import DataFrame


class QueueListenerHandler(QueueHandler):
    """
    QueueHandler, QueueListener 구현
    인자로 받은 handlers(logging.Handler)를 QueueListener에 등록 해서 로깅 이벤트 발생시
    둥록된 각 핸들러에서 이벤트를 처리한다.
    """
    def __init__(self, handlers, respect_handler_level=False, auto_run=True, queue=Queue(500)):
        queue = self._resolve_queue(queue)
        super().__init__(queue)

        # handlers = self._resolve_handlers(handlers)
        self._listener = QueueListener(
            queue,
            *handlers,
            respect_handler_level=respect_handler_level)

        if auto_run:
            self.start()
            atexit.register(self.stop)

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()

    def emit(self, record):
        return super().emit(record)

    @staticmethod
    def _resolve_queue(cfg_queue) -> Queue:
        """
        로깅용 Queue를 반환한다.

        logging_conf.yaml에 아래와 같이 설정한 경우

        objects:
                queue:
                    class: queue.Queue
                    maxsize: 1000

        QueueListenerHandler 생성시 파라미터 queue는 logging.config.ConvertingDict 인스턴스이므로
        queue.Queue 를 생성해서 반환한다.

        :param cfg_queue: ConvertingDict or Queue
        :return:
            Queue
        """
        if isinstance(cfg_queue, Queue):
            return cfg_queue

        cname = cfg_queue.pop('class')
        klass = cfg_queue.configurator.resolve(cname)
        props = cfg_queue.pop('.', None)
        kwargs = {key: cfg_queue[key] for key in cfg_queue if valid_ident(key)}
        obj = klass(**kwargs)
        if props:
            for name, value in props.items():
                setattr(obj, name, value)

        return obj

    # @staticmethod
    # def _resolve_handlers(handlers):
    #     if not isinstance(handlers, ConvertingList):
    #         return handlers
    #
    #     return [handlers[i] for i in range(len(handlers))]


class DefaultDBLogFormatter(logging.Formatter):
    DEFAULT_PROPERTIES = logging.LogRecord('', '', '', '', '', '', '', '').__dict__.keys()

    def format(self, record):
        document = {
            'timestamp': datetime.now(),
            'level': record.levelname,
            'thread': record.thread,
            'thread_name': record.threadName,
            'message': record.getMessage(),
            'logger_name': record.name,
            'file_name': record.pathname,
            'module': record.module,
            'method': record.funcName,
            'line_number': record.lineno,
            'exception': None,
            'trace': None
        }

        if record.exc_info is not None:
            document.update({
                'exception': str(record.exc_info[1]),
                'trace': self.formatException(record.exc_info)
            })

        return document


class MariaLogFormatter(DefaultDBLogFormatter):

    def format(self, record):
        document = super().format(record)
        df = DataFrame([document])
        return df


class MariaLogHandler(logging.Handler):

    def __init__(self, table='log', db='mariadb_log', host='localhost', level=logging.NOTSET):
        import sqlalchemy

        logging.Handler.__init__(self, level)
        self.formatter = MariaLogFormatter()
        self.table = table
        self.conn = sqlalchemy.create_engine(f'{host}/{db}', encoding='utf-8')

    def emit(self, record):
        try:
            df = self.format(record)
            df.to_sql(name=f'{self.table}', con=self.conn, if_exists='append', index=False)
        except Exception as err:
            logging.error("Unable to save log record: %s", str(err), exc_info=True)


class MongoLogFormatter(DefaultDBLogFormatter):

    def format(self, record):
        document = super().format(record)

        if len(self.DEFAULT_PROPERTIES) != len(record.__dict__):
            extra = set(record.__dict__).difference(set(self.DEFAULT_PROPERTIES))
            if extra:
                for key in extra:
                    document[key] = record.__dict__[key]

        return document


class MongoLogHandler(logging.Handler):

    def __init__(self, collection='logs', db='mongo_logs', host='localhost', level=logging.NOTSET):
        import pymongo

        logging.Handler.__init__(self, level)
        connection = pymongo.MongoClient(host)
        self.collection = connection[db][collection]
        self.formatter = MongoLogFormatter()

    def emit(self, record):
        try:
            self.collection.insert_one(self.format(record))
        except InvalidDocument as err:
            logging.error("Unable to save log record: %s", str(err), exc_info=True)


class DecoratorFormatter(logging.Formatter):

    def format(self, record):
        if hasattr(record, 'func_name_override'):
            record.funcName = record.func_name_override

        if hasattr(record, 'file_name_override'):
            record.filename = record.file_name_override

        if hasattr(record, 'lineno_override'):
            record.lineno = record.lineno_override

        return super(DecoratorFormatter, self).format(record)
