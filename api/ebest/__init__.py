import os
from pathlib import Path

import yaml

from skogkatt.commons.util.singleton import Singleton
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class QueryBuilder:
    def __init__(self, xa_query, transaction):
        self.xa_query = xa_query
        self.tr = transaction

    def build(self, *args, **kwargs):
        if len(args) != len(self.tr.api_params):
            raise ValueError(f'TR {self.tr.tr_code} Argument counts are different, required {len(self.tr.api_params)}, passed {len(args)}')

        in_block = self.tr.tr_code + self.tr.in_block
        self.xa_query.ResFileName = self.tr.res_file

        for i in range(len(args)):
            self.xa_query.SetFieldData(in_block, self.tr.api_params[i], 0, args[i])

        return self.xa_query


class Transaction:

    def __init__(self, tr_name, tr_code, api_params, params, in_block, res_file):
        self.tr_code = tr_code
        self.tr_name = tr_name
        self.api_params = api_params
        self.params = params
        self.in_block = in_block
        self.res_file = res_file


class TransactionFactory(object, metaclass=Singleton):

    def __init__(self, conf_file='tr_lookup.yaml'):
        self.tr_cache = {}
        self.config = None
        self.res_path = None

        dir_path = Path(os.path.dirname(os.path.relpath(__file__)))
        conf_file = dir_path.joinpath(conf_file)

        if os.path.exists(conf_file):
            logger.debug(f'Resolving DAO config file: {conf_file}')
            with open(conf_file, 'rt', encoding="utf-8") as file:
                self.config = yaml.safe_load(file.read())
                self.res_path = self.config.get('res_path')

    def get_res_path(self):
        return self.res_path

    def _resolve(self, key):
        tr_list: dict = self.config.get('transactions')
        if key not in tr_list:
            raise KeyError(f'{key} not found.')

        tran = None
        tr: dict = tr_list.pop(key)

        tran = Transaction(
            key,
            tr.get('tr_code'),
            tr.get('server_params'),
            tr.get('params'),
            tr.get('in_block'),
            f"{self.res_path}/{tr.get('tr_code')}.res"
        )

        self.tr_cache[key] = tran

        return tran

    def get(self, key):
        cached_tr = self.tr_cache.get(key, None)
        if cached_tr is not None:
            return cached_tr

        return self._resolve(key)


tr_factory = TransactionFactory()

