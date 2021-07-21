from queue import Queue

from skogkatt.batch import batch_lookup
from skogkatt.batch.queue_factory import queue_factory
from skogkatt.core import LoggerFactory
from skogkatt.core.dao import dao_factory
from skogkatt.core.decorators import batch_status
from skogkatt.core.ticker.store import ticker_store
from skogkatt.errors import PricerError
from skogkatt.screeners.rim.pricer import Pricer

logger = LoggerFactory.get_logger(__name__)


class RIMPriceEstimator:

    def __init__(self):
        self.name = batch_lookup.RIM_PRICER['name']
        self.pricer = Pricer()
        self.dao = dao_factory.get("RIMPriceEstimateDAO")

    @batch_status(batch_lookup.RIM_PRICER['name'])
    def start(self, queue: Queue = None):
        queue = queue if queue is not None else queue_factory.resolve_queue(self.name)
        logger.info(f'S-RIM Price reporting started - queued: {queue.qsize()}')

        unresolved_tickers = []
        for count in range(queue.qsize()):
            ticker = ticker_store.find_by_stock_code(queue.get().get('stock_code'))

            try:
                estimate = self.pricer.estimate(ticker)
                self.dao.update(estimate)
                queue_factory.remove_queue_item(self.name, ticker.code)
            except (PricerError, ValueError, KeyError, TypeError, IndexError) as err:
                error_data = ticker.to_dict()
                error_data['proc'] = self.name
                unresolved_tickers.append(error_data)
                logger.error(f'{ticker.code}-{str(err)}')

        if len(unresolved_tickers) > 0:
            logger.info(f'RIM 적정가 추정 실패 종목 수: {len(unresolved_tickers)}, error.log 확인.')


if __name__ == '__main__':
    batch = RIMPriceEstimator()
    batch.start()
