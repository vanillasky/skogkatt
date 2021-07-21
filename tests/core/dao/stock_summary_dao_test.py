import pytest

from skogkatt.conf.app_conf import app_config, Config
from skogkatt.tests.fnguide.sample_html_generator import load_html

app_config.set_mode(Config.TEST)

stock_code = "051910"


@pytest.fixture
def dao():
    from skogkatt.core.dao import dao_factory
    return dao_factory.get('StockSummaryDAO')


@pytest.fixture
def setup(fn_dto, request):

    yield fn_dto

    def teardown():
        pass
        # summary_dao = dao
        # summary_dao.delete()

    request.addfinalizer(teardown)


def test_update(setup, dao):
    """
    1개년도 재무제표 db insert
    :return:
    """
    dto = setup

    updated = dao.update(dto.stock_summary)
    updated = dao.update(dto.stock_summary)
    assert (1, updated)

    summary = dao.find([stock_code])
    print(summary)
    assert (1, len(summary))
    assert (stock_code, summary[0].stock_code)

    # def test_update(self):
    #     self.dao.update_summary(self.dto.stock_summary)
    #     self.dao.update_summary(self.dto.stock_summary)
    #
    #     summary = self.dao.find([self.test_stock_code])
    #     print(summary)
    #     self.assertEqual(1, len(summary))
    #     self.assertEqual(self.test_stock_code, summary[0].stock_code)
    #
    # def test_find_one(self):
    #     self.dao.update_summary(self.dto.stock_summary)
    #
    #     summary = self.dao.find_one(self.test_stock_code)
    #     self.assertEqual(self.test_stock_code, summary.stock_code)
    #     self.assertEqual(self.dto.stock_summary.common_stock_cnt, summary.common_stock_cnt)


