import logging
import logging.config
import os
from pathlib import Path

import yaml

from skogkatt.commons.util.singleton import Singleton


class BasicLoggerFactory(object, metaclass=Singleton):
    """
    설정파일 basic_logging_conf.yaml이 현재 디렉토리에 있을 때는 이 파일을 기반으로 로거를 설정하고
    설정파일이 없는 경우에는 기본 설정으로 세팅.

    설정파일을 사용할 때는 환경변수 LOG_FILE_PATH, MONGO_URL, MARIA_URL 필요.
    """

    def __init__(self):
        self._config = None
        self._logfile_dir = None
        self.configure()

    def configure(self):
        path = Path(__file__).parent
        conf_filepath = path.joinpath("basic_logging_conf.yaml")
        self._logfile_dir = os.getenv("LOG_FILE_PATH", path)

        if os.path.exists(conf_filepath):
            self._configure_dict_config(conf_filepath, self._logfile_dir)
        else:
            self._configure_basic()

    def _configure_dict_config(self, conf_filepath, logfile_dir):
        with open(conf_filepath, 'rt') as file:
            config = yaml.safe_load(file.read())
            config = self._set_path(config, logfile_dir)
            logging.config.dictConfig(config)
            self._config = config

    def _configure_basic(self):
        formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s")
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logging.basicConfig(level=logging.DEBUG, handlers=[console])
        self._config = None

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        factory = BasicLoggerFactory()
        return factory._resolve_logger(name)

    @staticmethod
    def get_config():
        factory = BasicLoggerFactory()
        return factory._config

    @staticmethod
    def get_logfile_dir():
        factory = BasicLoggerFactory()
        return factory._logfile_dir

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
                config["handlers"][name]["host"] = handler["host"].format(host_mongodb=os.getenv("MONGO_URL"))

            if 'host' in handler and '{host_mariadb}' in handler["host"]:
                config["handlers"][name]["host"] = handler["host"].format(host_mariadb=os.getenv("MARIA_URL"))

        return config
