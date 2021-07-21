from datetime import datetime
from queue import Queue
from typing import List

from skogkatt.commons.util.date import days_between
from skogkatt.commons.util.singleton import Singleton
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class QueueFactory(metaclass=Singleton):

    def __init__(self):

        from skogkatt.core.dao.idao import BatchQueueDAO
        from skogkatt.batch.monitor import BatchMonitor
        from skogkatt.core.dao import dao_factory

        self.queue_dao: BatchQueueDAO = dao_factory.get('BatchQueueDAO')
        self.monitor: BatchMonitor = BatchMonitor()

    def create(self, batch_name: str, except_stock_codes: List[str] = None) -> Queue:
        from skogkatt.core.ticker.store import ticker_store

        """
        주식 종목 코드를 배치 이름별로 큐를 만들어 반환한다.
        배치 실행 중 프로그램이 비정상 종료되는 경우에 대비해서 큐 자료는 DB에 저장

        :param batch_name: str, 배치명
        :param except_stock_codes: List[str], 큐 생성시 제외할 종목코드
        :return:
            queue.Queue
        """
        queue = Queue()
        tickers = ticker_store.get_tickers()
        ticker_list = []
        check_code = True if except_stock_codes is not None and len(except_stock_codes) > 0 else False
        count = 0

        for ticker in tickers:
            if check_code and ticker.code in except_stock_codes:
                continue

            queue_data = {'batch_name': batch_name, 'stock_code': ticker.code}
            ticker_list.append(queue_data)
            queue.put(queue_data)

            count += 1

        legacy_cnt = self.queue_dao.count(batch_name)
        if legacy_cnt > 0:
            logger.info(f'Queue data exist in DB, batch_name: {batch_name}. Delete legacy data.')
            self.queue_dao.delete(batch_name)
        else:
            logger.info(f'Queue created for: {batch_name}, size: {queue.qsize()}')
        self.queue_dao.insert(ticker_list)

        return queue

    def remove_queue_item(self, batch_name: str, stock_code: str = None):
        """
        해당 종목코드를 큐 DB에서 삭제한다.
        :param batch_name: str, 배치명
        :param stock_code: str, 종목코드
        :return:
            int, deleted record count
        """
        return self.queue_dao.delete(batch_name, stock_code)

    def remove_batch_queue(self, batch_name: str):
        """
        해당 종목코드를 큐 DB에서 삭제한다.
        :param batch_name: str, 배치명
        :return:
            int, deleted record count
        """
        return self.queue_dao.delete(batch_name)

    def get_queue(self, batch_name: str) -> Queue:
        queue = Queue()
        db_data = self.queue_dao.find(batch_name)
        [queue.put(each) for each in db_data]
        return queue

    def assign_queue(self, batch_name: str, stock_codes: List[str]):
        """
        작업큐에 해당 종목코드를 할당해서 반환한다.
        :param batch_name: str, 배치명
        :param stock_codes: List[str], 종목코드 리스트
        :return:
            Queue object
        """
        ticker_list = []
        queue = Queue()
        for code in stock_codes:
            queue_data = {'batch_name': batch_name, 'stock_code': code}
            ticker_list.append(queue_data)
            queue.put(queue_data)

        legacy_cnt = self.queue_dao.count(batch_name)
        if legacy_cnt > 0:
            logger.info(f'Queue data exist in DB, batch_name: {batch_name}. This data will be overwritten.')
            self.remove_batch_queue(batch_name)

        self.queue_dao.insert(ticker_list)

        return queue

    def resolve_queue(self,
                      batch_name: str,
                      batch_cycle: int = None,
                      batch_cycle_check: bool = False,
                      except_stock_codes: List[str] = None) -> Queue:
        """
        작업 큐를 반환한다.
        큐에 데이터가 남아있으면 그대로 반환하고 큐가 비어있으면 실행 주기를 확인해서
        실행이 필요하면 새로 큐를 만들어서 반환한다.
        :param batch_name: str, 배치명
        :param batch_cycle: 배치 실행 주기
        :param batch_cycle_check: bool, 배치 실행주기 체크 여부
        :param except_stock_codes: List[str], 큐 생성시 제외할 종목 코드
        :return: Queue object
        """
        queue = self.get_queue(batch_name)
        if queue.empty():
            status = self.monitor.get_status(batch_name)

            if status is None or status.end is None:
                logger.info(f'..status or status.end is None, create queue.')
                return self.create(batch_name, except_stock_codes)

            logger.info(f'Batch {batch_name} - last_updated: {status.end}')

            if batch_cycle_check:
                elapsed = days_between(status.end, datetime.today())
                if elapsed >= batch_cycle:
                    queue = self.create(batch_name, except_stock_codes)
                    logger.info(f'..batch execution cycle has arrived. cycle: {batch_cycle}, elapsed: {elapsed} days')
                else:
                    logger.info(f'..The batch execution cycle has not yet reached.')
            else:
                queue = self.create(batch_name, except_stock_codes)
                logger.info(f'..Batch cycle check is offed. Queue created for batch: {batch_name}')

        return queue


queue_factory = QueueFactory()
