import functools
import os
import traceback
from datetime import datetime
from inspect import getframeinfo, stack

from skogkatt.batch import BatchStatus
from skogkatt.batch.monitor import BatchMonitor
from skogkatt.commons.util.message import send_telegram_message
from skogkatt.conf.app_conf import app_config
from skogkatt.core import LoggerFactory


def batch_status(batch_name, logger_name='batch', notify=True):
    """
    배치작업 상태를 저장하는 Decorator.
    해당 함수의 시작/종료 시각, 상태, 에러 정보는 DB에 저장한다.
    :param batch_name: str, 작업명
    :param logger_name: str, logger name
    :param notify: Bool, 에러 발생 시 텔레그램 메세지 전송 여부
    :return:
    """
    def update_status(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            _logger = LoggerFactory.get_logger(logger_name)
            monitor = BatchMonitor()

            args_passed_in_function = [repr(a) for a in args]
            kwargs_passed_in_function = [f"{k}={v!r}" for k, v in kwargs.items()]
            formatted_arguments = ", ".join(args_passed_in_function + kwargs_passed_in_function)

            caller = getframeinfo(stack()[1][0])
            extra_args = {'func_name_override': func.__name__,
                          'file_name_override': os.path.basename(caller.filename),
                          'lineno_override': caller.lineno}

            _logger.info(f"Begin function {func.__name__} - Arguments: {formatted_arguments}", extra=extra_args)
            status = BatchStatus(batch_name, datetime.now())

            try:
                monitor.start(status)
                ret_value = func(*args, **kwargs)
                _logger.info(f"End function - Returned {ret_value!r}", extra=extra_args)
                status.status = 0
            except:
                status.status = -1
                status.trace = traceback.format_exc()

                _logger.error(status.trace)

                if notify:
                    try:
                        send_telegram_message(
                            [f'Error Occurred. function {func.__name__}', status.trace],
                            app_config.get('SKOGKATT_BOT_TOKEN')
                        )
                    except RuntimeError as err:
                        _logger.warning(str(err))

                raise

            status.end = datetime.now()
            status.elapsed = status.end - status.start
            _logger.debug(f'BatchStatus: {status}')
            monitor.end(status)

            return ret_value
        return wrapper
    return update_status
