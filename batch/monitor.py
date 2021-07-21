from skogkatt.batch import BatchStatus
from skogkatt.core.dao import dao_factory
from skogkatt.core.dao.idao import BatchStatusDAO


class BatchMonitor:

    def __init__(self):
        self.dao: BatchStatusDAO = dao_factory.get('BatchStatusDAO')

    def get_status(self, name: str) -> BatchStatus or None:
        result = self.dao.find(batch_name=name, limit=1)
        if len(result) > 0:
            return result[0]

        return None

    def end(self, status: BatchStatus):
        self.dao.update(status)

    def start(self, status: BatchStatus):
        self.dao.update(status)
