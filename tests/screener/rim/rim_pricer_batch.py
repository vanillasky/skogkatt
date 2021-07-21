from skogkatt.batch.queue_factory import queue_factory
from skogkatt.batch.rim_pricer import RIMPriceEstimator
from skogkatt.conf.app_conf import app_config, Config

app_config.set_mode(Config.TEST)


def test_rim_price_estimate():
    # 보험업종 - DB에 재무제표 자료 없음: 005830(DB손해보험), 000370(한화손해보험)
    stock_codes = ['005930', '051910']
    # stock_codes = ['005830']
    batch = RIMPriceEstimator()

    queue = queue_factory.assign_queue(batch.name, stock_codes)
    batch.start(queue)

