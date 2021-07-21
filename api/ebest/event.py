from datetime import datetime, timedelta

import pythoncom

from skogkatt.api.kiwoom import error_message
from skogkatt.api import ApiEvent, EventHandler
from skogkatt.commons.util.numeral import to_decimal
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class ConnectEvent(ApiEvent):

    def __init__(self):
        super().__init__()
        self.tr_received = False

    def fire_event(self, *args, **kwargs):
        message_code = kwargs.get('message_code')
        if message_code is not None:
            code = to_decimal(message_code)
            code = message_code if code is None else code

        self._error_code = 0 if kwargs.get('error') is None else code
        self._message = kwargs.get('message', None)
        self._data = kwargs
        self.notify()

    def wait_for_response(self, timeout_mills: int = 3000):
        now = datetime.now()
        timeout = now + timedelta(milliseconds=timeout_mills)

        while not self.tr_received and datetime.now() < timeout:
            pythoncom.PumpWaitingMessages()

    def OnLogin(self, code, msg):
        self.tr_received = True
        if code == "0000":
            self.fire_event(return_code=code)
        else:
            logger.error(f'Login Failed - code:{code}, {msg}')
            self.fire_event(error=msg, message_code=code)


class XAQueryEvent(ApiEvent):

    def __init__(self):
        super().__init__()
        self.tr_received = False

    def fire_event(self, *args, **kwargs):
        message_code = kwargs.get('message_code')
        if message_code is not None:
            code = to_decimal(message_code)
            code = message_code if code is None else code

        self._error_code = 0 if kwargs.get('error') is None else code
        self._message = kwargs.get('message', None)
        self._data = kwargs
        self.notify()

    def wait_for_response(self, timeout_mills: int = 3000):
        now = datetime.now()
        timeout = now + timedelta(milliseconds=timeout_mills)

        while not self.tr_received and datetime.now() < timeout:
            pythoncom.PumpWaitingMessages()

    def OnReceiveData(self, tr_code):
        logger.debug(f'OnReceiveData: {tr_code}')
        self.tr_received = True
        self.fire_event(tr_code=tr_code, query=self)

    def OnReceiveMessage(self, system_error, message_code, message):
        logger.debug(f'OnReceiveMessage: {system_error}, {message_code}, {message}')
        self.fire_event(error=system_error, message_code=message_code, message=message)

