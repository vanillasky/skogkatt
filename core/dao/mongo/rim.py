from skogkatt.core.dao.engine import MongoEngine
from skogkatt.core.dao.idao import RIMPriceEstimateDAO
from skogkatt.screeners.rim import PriceEstimate


class MongoRIMPriceEstimateDAO(RIMPriceEstimateDAO):
    def __init__(self, db_name=None, table='rim_price'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = table
        self.conn = self._engine.get_connection()

    def update(self, price: PriceEstimate) -> int:
        query = {'stock_code': price.stock_code}
        result = self._table.update_one(query, {"$set": price.to_dict()}, upsert=True)
        return 1 if result.upserted_id is not None else 0

