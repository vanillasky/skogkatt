from skogkatt.batch import BatchStatus, batch_lookup
from skogkatt.crawler import TickerCrawler


def test_crawl():
    from skogkatt.batch.monitor import BatchMonitor
    crawler = TickerCrawler()
    df = crawler.crawl()
    assert (7, df.shape[1])

    monitor = BatchMonitor()
    status: BatchStatus = monitor.get_status(batch_lookup.TICKER['name'])
    assert (status.end is not None)

