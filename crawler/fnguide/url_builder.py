from skogkatt.conf.crawl_conf import FN_SNAPSHOT_URL, FN_SNAPSHOT_PARAMS, FN_STATEMENT_URL, FN_STATEMENT_PARAMS
from skogkatt.crawler.util import UrlBuilder


class FnSnapshotUrlBuilder(UrlBuilder):

    def __init__(self):
        super().__init__()
        self._url = FN_SNAPSHOT_URL
        self._payload = FN_SNAPSHOT_PARAMS

    def build(self, **kwargs):
        stock_code = kwargs.get('stock_code', None)
        if stock_code is None:
            raise KeyError('stock_code is required')
        self._payload['gicode'] = f'A{stock_code}'

        return self._url, self._payload


class FnStatementUrlBuilder(UrlBuilder):

    def __init__(self):
        super().__init__()
        self._url = FN_STATEMENT_URL
        self._payload = FN_STATEMENT_PARAMS

    def build(self, **kwargs):
        stock_code = kwargs.get('stock_code', None)
        if stock_code is None:
            raise KeyError('stock_code is required.')
        self._payload['gicode'] = f'A{stock_code}'

        return self._url, self._payload
