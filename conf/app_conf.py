import os
from pathlib import Path

from dotenv import load_dotenv, dotenv_values, find_dotenv

from skogkatt.commons.util.singleton import Singleton


def get_project_path():
    return Path(__file__).parent.parent


class Config(metaclass=Singleton):
    PROD = 0
    DEV = 1
    TEST = 2

    def __init__(self):
        self._current_mode = None
        self._initial_mode = None

        env_file = find_dotenv(filename='.env.development')
        self.dev_values = dotenv_values(env_file, verbose=True)
        load_dotenv(override=True)

        default_mode = os.getenv('ENVIRONMENT')
        if default_mode is None or default_mode == 'PROD':
            self._initial_mode = Config.PROD
        else:
            self._initial_mode = Config.DEV

        self._current_mode = self._initial_mode

    def get(self, key):
        if self._current_mode == Config.PROD:
            return os.getenv(key)

        value = self.dev_values.get(key, None)

        if value is None:
            return os.getenv(key)
        else:
            return value

    def restore(self):
        self._current_mode = self._initial_mode

    def set_mode(self, mode: int):
        self._current_mode = mode

    @property
    def current_mode(self):
        return self._current_mode


app_config = Config()
