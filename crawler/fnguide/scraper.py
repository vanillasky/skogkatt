import random
import time
from pathlib import Path
from queue import Queue

from bs4 import BeautifulSoup

from requests import Timeout, HTTPError, RequestException
from requests.exceptions import ProxyError

from skogkatt.conf.crawl_conf import (
    FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH, FNGUIDE_SNAPSHOT_FILE_PREFIX,
    FNGUIDE_STATEMENT_FILE_STORAGE_PATH, FNGUIDE_STATEMENT_FILE_PREFIX, PROXIES
)

from skogkatt.batch import batch_lookup
from skogkatt.batch.queue_factory import queue_factory
from skogkatt.crawler.fnguide.url_builder import FnSnapshotUrlBuilder, FnStatementUrlBuilder
from skogkatt.crawler.util import UrlBuilder, renew_connection
from skogkatt.core.decorators import batch_status
from skogkatt.core import LoggerFactory
from skogkatt.commons.http.request import request
from skogkatt.commons.util.file import save_file
from skogkatt.errors import CrawlerError

logger = LoggerFactory.get_logger(__name__)

IP_RENEW_INTERVAL = 300

"""
FnGuide 사이트에서 Snapshot, 재무제표 html 파일을 크롤링해서 파일로 저장한다.
분기별 업데이트 일정을 참고하여 FnGuide에서 분기자료 업데이트 확인 후 개별 실행 권장:
 - 접속차단 방지를 위해 5분마다 IP를 바꾸고, 1건 수집 후 1~4초간 쉬기 때문에 시간 오래 걸림
 - Terminal에서 실행시 Tor 네트워크 설정(renew_connection 메소드) 실행시 에러 발생하므로 IDE에서 실행
 
--- 업데이트 일정 ---
# 1분기 자료 - 5월 15일경
# 2분기 자료 - 8월 15일
# 3분기 자료 - 11월 15일
# 4분기 자료 - 3월 중순

"""


def batch_crawl(batch_name: str,
                file_path: str,
                file_name_prefix: str,
                url_builder: UrlBuilder,
                ip_renew_interval: int = IP_RENEW_INTERVAL,
                queue: Queue = None,):
    """
    큐에 담긴 주식 종목코드를 읽어 파일로 저장한다.
    배치 주기, 주기 확인여부를 적용하여 batch_name을 Key로 DB에 큐 데이터를 만들고 이를 사용한다.

    :param batch_name: str, 배치이름
    :param file_path: str, 파일 저장 경로
    :param file_name_prefix: str, 저장할 파일명 prefix
    :param url_builder: UrlBuilder, parameter를 생성해주는 UrlBuilder
    :param ip_renew_interval: int, optional, IP 갱신 주기 in seconds
    :param queue: Queue, optional, 별도의 큐를 사용할 경우
    :return:
        int, 큐에 남아있는 아이템 개수
    """
    queue = queue if queue is not None else queue_factory.resolve_queue(batch_name)

    if queue.empty():
        logger.info(f'Queue for {batch_name} is empty, return.')
        return

    file_path = Path(file_path)
    ip_time = time.time()

    for count in range(queue.qsize()):
        stock_code = queue.get().get('stock_code')
        url, payload = url_builder.build(stock_code=stock_code)
        filename = f'{file_name_prefix}{stock_code}.html'

        try:
            current = time.time()
            elapsed = current - ip_time
            if elapsed > ip_renew_interval:
                logger.debug(f'IP used {elapsed / 60} minutes, renew tor IP')
                renew_connection()
                ip_time = current

            res = request.get(url=url, payload=payload, proxies=PROXIES)
            soup = BeautifulSoup(res.content, "html5lib")
            save_file(str(soup), file_path=file_path, file_name=filename)

            queue_factory.remove_queue_item(batch_name, stock_code)

            sleep = random.randrange(1, 4)
            time.sleep(sleep)

        except ProxyError as err:
            logger.fatal(f'Proxy Server is not running, check your proxies: {err}')
            raise
        except (Timeout, ConnectionError, HTTPError, RequestException) as err:
            logger.fatal(f'Cannot scrape FnGuide Data: {err}')
            raise

    return queue.qsize()


def scrape_by(stock_code: str,
              file_path: str,
              file_name_prefix: str,
              url_builder: UrlBuilder,
              use_proxy: bool = True):

    url, payload = url_builder.build(stock_code=stock_code)
    filename = f'{file_name_prefix}{stock_code}.html'
    file_path = Path(file_path)

    try:
        if use_proxy:
            res = request.get(url=url, payload=payload, proxies=PROXIES)
        else:
            res = request.get(url=url, payload=payload, proxies=None)

        soup = BeautifulSoup(res.content, "html5lib")
        save_file(str(soup), file_path=file_path, file_name=filename)
        return file_path.joinpath(filename)

    except (Timeout, ConnectionError, HTTPError, RequestException) as err:
        raise CrawlerError(f'Cannot scrape FnGuide Data.', stock_code=stock_code)


class FnGuideSnapshotScraper:

    def __init__(self):
        pass

    @batch_status(batch_lookup.FN_GUIDE_SNAPSHOT['name'])
    def start(self, queue: Queue = None, file_path: str = FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH):
        """
        FnGuide 스냅샷 수집
        :param queue: 종목코드 Queue. contained {'batch_name': batch_name, 'stock_code': code}
        :param file_path: str, html 파일 저장 경로
        :return:
            큐에 남아있는 아이템 개수
        """
        remained = \
            batch_crawl(batch_name=batch_lookup.FN_GUIDE_SNAPSHOT['name'],
                        file_path=file_path,
                        file_name_prefix=FNGUIDE_SNAPSHOT_FILE_PREFIX,
                        url_builder=FnSnapshotUrlBuilder(),
                        ip_renew_interval=IP_RENEW_INTERVAL,
                        queue=queue)

        return remained

    @staticmethod
    def scrape(stock_code):
        return scrape_by(stock_code,
                         file_path=FNGUIDE_SNAPSHOT_FILE_STORAGE_PATH,
                         file_name_prefix=FNGUIDE_SNAPSHOT_FILE_PREFIX,
                         url_builder=FnSnapshotUrlBuilder())


class FnGuideStatementScraper:

    def __init__(self):
        pass

    @batch_status(batch_lookup.FN_GUIDE_STATEMENT['name'])
    def start(self, queue: Queue = None, file_path: str = FNGUIDE_STATEMENT_FILE_STORAGE_PATH):
        remained = \
            batch_crawl(batch_name=batch_lookup.FN_GUIDE_STATEMENT['name'],
                        file_path=file_path,
                        file_name_prefix=FNGUIDE_STATEMENT_FILE_PREFIX,
                        url_builder=FnStatementUrlBuilder(),
                        ip_renew_interval=IP_RENEW_INTERVAL,
                        queue=queue)

        return remained

    @staticmethod
    def scrape(stock_code):
        return scrape_by(stock_code,
                         file_path=FNGUIDE_STATEMENT_FILE_STORAGE_PATH,
                         file_name_prefix=FNGUIDE_STATEMENT_FILE_PREFIX,
                         url_builder=FnStatementUrlBuilder())

    def reinforce(self):
        queue_factory.delete('fn-statement-scrape')
        queue = queue_factory.get_queue('fn-statement-convert')
        stock_codes = []
        for count in range(queue.qsize()):
            stock_codes.append(queue.get().get('stock_code'))

        queue = queue_factory.assign_queue('fn-statement-scrape', stock_codes)
        self.start(queue)


# if __name__ == '__main__':
#     batch = FnGuideStatementScraper()
#     batch.start()
    # batch.reinforce()


