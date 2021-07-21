from typing import List

import pandas as pd

from skogkatt.batch import BatchStatus
from skogkatt.core import LoggerFactory
from skogkatt.core.dao.engine import MariaEngine
from skogkatt.core.dao.idao import BatchStatusDAO, BatchQueueDAO
from skogkatt.core.dao.maria import make_query

logger = LoggerFactory.get_logger(__name__)


class MariaBatchStatusDAO(BatchStatusDAO):

    def __init__(self, db_name=None, table='batch_status'):
        super().__init__()
        self._engine = MariaEngine(db_name)
        self._table_name = table
        self.conn = self._engine.get_connection()

    def find(self, batch_name: str = None, limit: int = None, as_dataframe=False):
        status_list = []
        query = []
        params = []

        sql = "select * from {} where 1=1 {} order by start desc"

        if batch_name is not None:
            query.append(" and name = %s")
            params.append(batch_name)

        sql = sql.format(self._table_name, ''.join(query))
        if limit is not None:
            sql += f" limit {limit}"

        if as_dataframe:
            return pd.read_sql(sql, self.conn, params=params)

        result = self.conn.execute(sql, params).fetchall()

        for record in result:
            status_list.append(BatchStatus(record[0], record[1], record[2], record[3], record[4]))

        return status_list

    def update(self, status: BatchStatus):
        sql = f"insert into {self._table_name} (name, start, end, elapsed, status, trace) " \
              f"values (%s, %s, %s, %s, %s, %s) " \
              f"on duplicate key update end = %s, elapsed = %s, status = %s, trace = %s"

        params = (status.name, status.start, status.end, status.elapsed, status.status, status.trace,
                  status.end, status.elapsed, status.status, status.trace)

        self.conn.execute(sql, params)

    def insert(self, status: BatchStatus):
        sql = f"insert into {self._table_name} (name, start, status) " \
              f"values (%s, %s, %s)"

        self.conn.execute(sql, (status.name, status.start, status.status))

    def delete(self, name: str = None):
        sql = f"delete from {self._table_name} where 1=1"

        conditions, params = make_query('eq', name=name)

        sql = sql + ' '.join(conditions)
        result = self.conn.execute(sql, params)
        logger.debug(f'Deleted: {result.rowcount}')

    def count(self, batch_name: str = None):
        query = []
        params = []

        sql = f"select count(*) as cnt from {self._table_name} where 1=1"

        if batch_name is not None:
            query.append(" and batch_name = %s")
            params.append(batch_name)

        result = self.conn.execute(sql, params).fetchall()
        return result[0][0]


class MariaBatchQueueDAO(BatchQueueDAO):

    def __init__(self, db_name=None, table='batch_queue'):
        super().__init__()
        self._engine = MariaEngine(db_name)
        self._table_name = table
        self.conn = self._engine.get_connection()

    def insert(self, queue_data: List):

        sql = f"insert into {self._table_name} (batch_name, stock_code) values (%s, %s)"
        values = []
        for each in queue_data:
            values.append((each['batch_name'], each['stock_code']))
        result = self.conn.execute(sql, values)

        print(result.rowcount)
        # df = DataFrame(queue_data)
        # df.to_sql(name=f'{self._table_name}', con=self.conn, if_exists='replace', index=False)

    def delete(self, batch_name: str = None, stock_code: str = None):
        sql = f"delete from {self._table_name} where 1=1"
        conditions, params = make_query('eq', batch_name=batch_name, stock_code=stock_code)
        sql = sql + ' '.join(conditions)
        result = self.conn.execute(sql, params)
        logger.debug(f'Deleted: {result.rowcount}')

    def find(self, batch_name: str):
        query = []
        params = []

        sql = f"select * from {self._table_name} where 1=1"

        if batch_name is not None:
            query.append(" and batch_name = %s")
            params.append(batch_name)

        sql = sql + ' '.join(query)
        result = self.conn.execute(sql, params).fetchall()
        return result

    def update(self, *args, **kwargs):
        raise NotImplementedError()

    def count(self, batch_name: str):
        sql = f"select count(stock_code) as cnt from {self._table_name} where 1=1"
        conditions, params = make_query('eq', batch_name=batch_name)

        sql = sql + ' '.join(conditions)
        result = self.conn.execute(sql, params).fetchall()
        return result[0][0]



