from typing import List

import pymongo
from pandas import DataFrame

from skogkatt.batch import BatchStatus
from skogkatt.core.dao.engine import MongoEngine
from skogkatt.core.dao.idao import BatchStatusDAO, BatchQueueDAO


class MongoBatchStatusDAO(BatchStatusDAO):

    def __init__(self, db_name=None, table='batch_status'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = self._table.name
        self.conn = self._engine.get_connection()

    def find(self, batch_name: str = None, limit: int = None, as_dataframe=False):
        status_list = []
        _filter = {}
        if batch_name is not None:
            _filter['name'] = batch_name

        cursor = self._table.find(_filter, {"_id": 0}).sort([('start', pymongo.DESCENDING)])
        if limit is not None:
            cursor = cursor.limit(limit)

        result = list(cursor)
        if as_dataframe:
            return DataFrame(result)

        for status in result:
            status_list.append(BatchStatus.from_dict(status))

        return status_list

    def update(self, status: BatchStatus) -> int:
        query = {'name': status.name, 'start': status.start}
        data = status.to_dict()
        result = self._table.update_one(query, {"$set": data}, upsert=True)
        return 1 if result.upserted_id is not None else 0

    def insert(self, status: BatchStatus) -> int:
        result = self._table.insert_one(status.to_dict())
        return 1 if result.inserted_id is not None else 0

    def delete(self, name: str = None) -> int:
        query = {}
        if name is not None:
            query['name'] = name

        result = self._table.delete_many(query)
        return result.deleted_count

    def count(self, batch_name: str = None) -> int:
        _filter = {}
        if batch_name is not None:
            _filter['name'] = batch_name

        return self._table.count_documents(_filter)


class MongoBatchQueueDAO(BatchQueueDAO):

    def __init__(self, db_name=None, table='batch_queue'):
        super().__init__()
        self._engine = MongoEngine(db_name)
        self._table = self._engine.get_db()[table]
        self._table_name = self._table.name
        self.conn = self._engine.get_connection()

    def insert(self, queue_data: List):
        result = self._table.insert_many(queue_data)
        return len(result.inserted_ids)

    def delete(self, batch_name: str, stock_code: str = None):
        query = {'batch_name': batch_name}
        if stock_code is not None:
            query['stock_code'] = stock_code

        result = self._table.delete_many(query)
        return result.deleted_count

    def find(self, batch_name: str):
        return list(self._table.find({'batch_name': batch_name}))

    def update(self, *args, **kwargs):
        raise NotImplementedError()

    def count(self, batch_name: str):
        return self._table.count_documents({'batch_name': batch_name})
