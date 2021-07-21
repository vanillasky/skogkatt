import shutil
import pytest

from skogkatt.batch import batch_lookup, BatchStatus
from skogkatt.batch.monitor import BatchMonitor
from skogkatt.batch.queue_factory import queue_factory
from skogkatt.conf.app_conf import get_project_path
from skogkatt.conf.crawl_conf import FNGUIDE_SNAPSHOT_FILE_PREFIX, FNGUIDE_STATEMENT_FILE_PREFIX
from skogkatt.crawler.fnguide.scraper import FnGuideSnapshotScraper, FnGuideStatementScraper

TEST_STOCK_CODES = ['005930', '051910']


@pytest.fixture
def queue_fixture():
    def _queue_fixture(batch_name):
        queue = queue_factory.assign_queue(batch_name, TEST_STOCK_CODES)
        return queue

    return _queue_fixture


@pytest.fixture()
def snapshot_scraper():
    return FnGuideSnapshotScraper()


@pytest.fixture()
def statement_scraper():
    return FnGuideStatementScraper()


@pytest.fixture
def crawl_snapshot(queue_fixture, snapshot_scraper, request):
    storage_path = get_project_path().parent.joinpath('fn_snapshot')
    batch_name = batch_lookup.FN_GUIDE_SNAPSHOT['name']
    queue = queue_fixture(batch_name)
    remained = snapshot_scraper.start(queue=queue, file_path=storage_path)
    filenames = [f'{FNGUIDE_SNAPSHOT_FILE_PREFIX}{stock_code}.html' for stock_code in TEST_STOCK_CODES]
    file_paths = [storage_path.joinpath(f'{filename}') for filename in filenames]

    yield storage_path, batch_name, file_paths, remained

    shutil.rmtree(storage_path)


@pytest.fixture
def crawl_statement(queue_fixture, statement_scraper, request):
    storage_path = get_project_path().parent.joinpath('fn_statement')
    batch_name = batch_lookup.FN_GUIDE_STATEMENT['name']
    queue = queue_fixture(batch_name)
    remained = statement_scraper.start(queue=queue, file_path=storage_path)
    filenames = [f'{FNGUIDE_STATEMENT_FILE_PREFIX}{stock_code}.html' for stock_code in TEST_STOCK_CODES]
    file_paths = [storage_path.joinpath(f'{filename}') for filename in filenames]

    yield storage_path, batch_name, file_paths, remained

    shutil.rmtree(storage_path)


def test_crawl_snapshot(crawl_snapshot):
    storage_path, batch_name, file_paths, remained = crawl_snapshot
    """
    FN-GUIDE 스냅샷 수집 결과 확인
      1) batch_status 테이블 배치명, 종료일, 상태 업데이트 여부
      2) 디스크에 파일 html 파일 저장여부
      3) 작업 큐가 비었는지 확인
      4) 테스트 디렉토리 삭제
    """
    assert (0 == remained)

    for file in file_paths:
        assert (file.exists())

    monitor = BatchMonitor()
    status: BatchStatus = monitor.get_status(batch_name)
    assert (0 == status.status)
    queue = queue_factory.get_queue(batch_name)
    assert (queue.empty())


def test_crawl_statement(crawl_statement):
    storage_path, batch_name, file_paths, remained = crawl_statement
    """
    FN-GUIDE 스냅샷 수집 결과 확인
      1) batch_status 테이블 배치명, 종료일, 상태 업데이트 여부
      2) 디스크에 파일 html 파일 저장여부
      3) 작업 큐가 비었는지 확인
      4) 테스트 디렉토리 삭제
    """
    assert (0 == remained)

    for file in file_paths:
        assert (file.exists())

    monitor = BatchMonitor()
    status: BatchStatus = monitor.get_status(batch_name)
    assert (0 == status.status)
    queue = queue_factory.get_queue(batch_name)
    assert (queue.empty())
