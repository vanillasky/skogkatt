
from skogkatt.conf.crawl_conf import FN_SNAPSHOT_URL
from skogkatt.crawler.fnguide.url_builder import FnSnapshotUrlBuilder


def test_build():
    builder = FnSnapshotUrlBuilder()
    url, payload = builder.build(stock_code="005930")

    assert (FN_SNAPSHOT_URL == url)
    assert ("A005930", payload.get('gicode'))


