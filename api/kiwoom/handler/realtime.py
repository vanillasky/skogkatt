from skogkatt.api.kiwoom.event import ApiEvent
from skogkatt.api import EventHandler
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RealTimeDataHandler(EventHandler):

    def __init__(self):
        super().__init__()

    def update(self, event: ApiEvent) -> None:
        data = event.data
        print(data.get('stock_code'))
        print(data.get('real_type'))
        print(data.get('real_data'))
        print(data.get('price'))

    def get_result(self):
        return {"data": None, "error": None}
