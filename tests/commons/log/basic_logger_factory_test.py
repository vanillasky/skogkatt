import logging
import os
from pathlib import Path

from skogkatt.commons.log.base import BasicLoggerFactory


def test_basic_config():
    logger = BasicLoggerFactory.get_logger(__name__)
    logger.debug("Debug Message")
    config = BasicLoggerFactory.get_config()
    assert (1.0 == config.get("version"))

    file_dir = BasicLoggerFactory.get_logfile_dir()
    file = Path(file_dir).joinpath('debug.log')
    assert (os.path.isfile(file))

    logger = logging.getLogger()
    log_handlers = logger.handlers
    for handler in log_handlers:
        handler.close()
        logger.removeHandler(handler)

    file_dir = BasicLoggerFactory.get_logfile_dir()
    file = Path(file_dir).joinpath('debug.log')
    os.remove(file)
