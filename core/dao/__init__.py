import os
from logging.config import valid_ident
from typing import Any

import yaml


from skogkatt.commons.util import instantiate
from skogkatt.commons.util.singleton import Singleton
from skogkatt.conf.app_conf import get_project_path
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class DAOFactory(object, metaclass=Singleton):

    def __init__(self, conf_files=('conf/dao_conf.yaml',)):
        self._creators = {}
        # self._config = None

        root_path = get_project_path()
        for config_file in conf_files:
            conf_file_path = root_path.joinpath(config_file)
            print(conf_file_path)
            if os.path.exists(conf_file_path):
                logger.debug(f'Resolving DAO config file: {config_file}')
                with open(conf_file_path, 'rt') as file:
                    config = yaml.safe_load(file.read())
                    # self._config = yaml.safe_load(file.read())
                    # config = deepcopy(self._config)
                    self.configure(config)

    def configure(self, config: dict):
        dao_list = config.pop('dao_list')
        for key, class_list in dao_list.items():
            class_name = class_list.pop('class')

            kwargs = {k: class_list[k] for k in class_list if valid_ident(k)}
            instance = instantiate(class_name, kwargs)
            self.register_dao(key, instance)

    def get(self, key: str):
        dao = self._creators.get(key)
        if not dao:
            raise KeyError(key)
        return dao

    def register_dao(self, key: str, dao: Any):
        self._creators[key] = dao


# dao_factory = DAOFactory(['conf/maria_dao_conf.yaml'])
dao_factory = DAOFactory()
