from datetime import datetime
from queue import Queue

from skogkatt.batch import batch_lookup
from skogkatt.batch.queue_factory import queue_factory
from skogkatt.crawler.fnguide.parser import FnSnapshotParser, FnStatementParser
from skogkatt.core.dao.idao import StockSummaryDAO, FnStatementDAO, FnStatementAbbrDAO
from skogkatt.core.dao import dao_factory
from skogkatt.core.decorators import batch_status
from skogkatt.errors import StatementParseError
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def save_failed_ticker(failed_codes):
    dao = dao_factory.get('FailedTickerDAO')
    dao.update(failed_codes)


@batch_status(batch_lookup.FN_SNAPSHOT_CONVERT['name'])
def convert_snapshot(queue: Queue = None):
    """
    FnGuide에서 수집한 FnSnapshot HTML 자료를 변환하여 DB에 저장한다.
    :param queue: Queue, optional, 처리할 주식코드를 별도로 지정할 때 사용
    :return:
        List[처리된 종목코드]
    """
    job_name = batch_lookup.FN_SNAPSHOT_CONVERT['name']
    queue = queue if queue is not None else queue_factory.resolve_queue(job_name)

    if queue.empty():
        logger.info(f'Queue for {job_name} is empty, return.')
        return

    processed_codes = []
    failed_codes = []
    summary_dao: StockSummaryDAO = dao_factory.get('StockSummaryDAO')
    statement_dao: FnStatementAbbrDAO = dao_factory.get('FnStatementAbbrDAO')
    parser = FnSnapshotParser()

    logger.info(f'FnGuide Snapshot HTML parse and save to DB - queued: {queue.qsize()}')

    for count in range(queue.qsize()):
        start = datetime.now()
        stock_code = queue.get().get('stock_code')
        try:
            # filename = f'{filename_prefix}{stock_code}.html'
            dto = parser.parse(stock_code)
            summary_dao.update(dto.stock_summary)
            statement_dao.update(dto.annual_abbreviations)
            statement_dao.update(dto.quarter_abbreviations)

            queue_factory.remove_queue_item(job_name, stock_code)
            processed_codes.append(stock_code)
        except FileNotFoundError as err:
            logger.error(str(err))
            failed_codes.append({'date': start, 'job_name': job_name, 'stock_code': stock_code, 'cause': 'FileNotFound'})
        except StatementParseError as err:
            logger.error(str(err))
            failed_codes.append({'date': start, 'job_name': job_name, 'stock_code': stock_code, 'cause': str(err)})

        elapsed = datetime.now() - start
        logger.debug(f'..Snapshot converted - {stock_code}, elapsed:{elapsed}')

    if not queue.empty():
        logger.info(f'There are unresolved financial snapshots: {queue.qsize()}, check error.log')
        save_failed_ticker(failed_codes)
        queue_factory.remove_batch_queue(job_name)

    return processed_codes


@batch_status(batch_lookup.FN_STATEMENT_CONVERT['name'])
def convert_statement(queue: Queue = None):
    """
    FnGuide에서 수집한 재무제표 HTML 자료를 변환하여 DB에 저장한다.
    :param queue: Queue, optional, 처리할 주식코드를 별도로 지정할 때 사용
    :return:
        List[처리된 종목코드]
    """
    job_name = 'fn-statement-convert'
    queue = queue if queue is not None else queue_factory.resolve_queue(job_name)

    if queue.empty():
        logger.info(f'Queue for {job_name} is empty, return.')
        return

    processed_codes = []
    failed_codes = []
    statement_dao: FnStatementDAO = dao_factory.get('FnStatementDAO')
    parser = FnStatementParser()

    logger.info(f'FnGuide Statement HTML parse and save to DB - queued: {queue.qsize()}')

    for count in range(queue.qsize()):
        start = datetime.now()
        stock_code = queue.get().get('stock_code')
        try:
            # filename = f'{filename_prefix}{stock_code}.html'
            dto = parser.parse(stock_code)
            statement_dao.update(dto.annual_statements)
            statement_dao.update(dto.quarter_statements)

            queue_factory.remove_queue_item(job_name, stock_code)
            processed_codes.append(stock_code)
        except FileNotFoundError as err:
            logger.error(str(err))
            failed_codes.append(
                {'date': start, 'job_name': job_name, 'stock_code': stock_code, 'cause': 'FileNotFound'})
        except StatementParseError as err:
            logger.error(str(err))
            failed_codes.append({'date': start, 'job_name': job_name, 'stock_code': stock_code, 'cause': str(err)})

        elapsed = datetime.now() - start
        logger.debug(f'..Statement converted - {stock_code}, elapsed:{elapsed}')

    if not queue.empty():
        logger.info(f'There are unresolved financial statements: {queue.qsize()}, check error.log')
        save_failed_ticker(failed_codes)
        queue_factory.remove_batch_queue(job_name)

    return processed_codes


if __name__ == '__main__':
    # convert_snapshot()
    convert_statement()
