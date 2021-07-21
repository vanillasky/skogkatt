import logging
import logging.config
import os

from skogkatt.commons.log.base import BasicLoggerFactory
from skogkatt.commons.util.singleton import Singleton
from skogkatt.conf.app_conf import app_config, get_project_path


class LoggerFactory(BasicLoggerFactory, metaclass=Singleton):

    def __init__(self):
        super().__init__()
        self.configure()

    def configure(self):
        path = get_project_path()
        conf_filepath = path.joinpath("conf/logging_conf.yaml")
        self._logfile_dir = app_config.get("LOG_FILE_PATH")

        if os.path.exists(conf_filepath):
            self._configure_dict_config(conf_filepath, self._logfile_dir)
        else:
            self._configure_basic()

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        factory = LoggerFactory()
        return factory._resolve_logger(name)

    @staticmethod
    def get_config():
        factory = LoggerFactory()
        return factory._config

    @staticmethod
    def _resolve_logger(name):
        return logging.getLogger(name)

    def _set_path(self, config, logfile_dir):
        if not os.path.exists(logfile_dir):
            os.mkdir(logfile_dir)

        for name in config["handlers"]:
            handler = config["handlers"][name]
            if 'filename' in handler and '{path}' in handler["filename"]:
                config["handlers"][name]["filename"] = handler["filename"].format(path=logfile_dir)

            if 'host' in handler and '{host_mongodb}' in handler["host"]:
                config["handlers"][name]["host"] = handler["host"].format(host_mongodb=app_config.get("MONGO_URL"))

            if 'host' in handler and '{host_mariadb}' in handler["host"]:
                config["handlers"][name]["host"] = handler["host"].format(host_mariadb=app_config.get("MARIA_URL"))

        return config
