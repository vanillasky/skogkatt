from abc import ABCMeta, abstractmethod
from typing import List, Any

from skogkatt.api.account import Account
from skogkatt.api.order import Order


class Broker(metaclass=ABCMeta):

    @abstractmethod
    def connect(self, block=True) -> dict:
        """
        서버 연결/로그인 수행
        :param block:
        :return:
            dict, {'data': error_code, 'error': error_message}
        """
        pass

    @abstractmethod
    def get_connect_state(self) -> int:
        """
        서버 접속 상태를 반환한다.
        :return:
            int, 0: 미연결, 1: 연결완료
        """
        pass

    @abstractmethod
    def get_server_type(self) -> int:
        """
        서버구분을 반환한다. 1: 모의투자, 나머지: 실서버
        :return:
        """
        pass

    @abstractmethod
    def get_accounts(self) -> List[str]:
        """
        계좌 목록 조회
        :return:
            List[str]
        """
        pass

    @abstractmethod
    def get_user_id(self) -> str:
        pass

    @abstractmethod
    def get_account_balance(self, *args, **kwargs):
        pass

    # @abstractmethod
    # def get_deposit_day2(self, account_no):
    #     pass

    @abstractmethod
    def get_chart(self, *args, **kwargs) -> dict:
        """
        챠트 조회
        :return:
            data, error_code, message
        """
        pass

    @abstractmethod
    def send_order(self, *args, **kwargs):
        """
        주문 전송
        :return:
            data, error_code, message
        """
        pass

    @abstractmethod
    def get_filter_formulas(self, *args, **kwargs):
        """
        조건검색 목록을 반환한다.
        :return:
        """
        pass

    @abstractmethod
    def get_filtered_tickers(self, *args, **kwargs):
        """
        조건검색에 부합하는 종목을 반환한다.
        :return:
        """
        pass

    @abstractmethod
    def get_current_price(self, stock_codes: List[str]):
        pass


class ApiEvent(metaclass=ABCMeta):

    def __init__(self):
        self._error_code: int = None
        self._message: str = None
        self._data = None
        self._observers = []

    def register(self, observer) -> None:
        self._observers.append(observer)

    def remove(self, observer) -> None:
        self._observers.remove(observer)

    def clear(self) -> None:
        self._observers.clear()

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)

    @abstractmethod
    def fire_event(self, *args, **kwargs):
        pass

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def error_code(self):
        return self._error_code

    @error_code.setter
    def error_code(self, code: int):
        self._error_code = code

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        self._message = message


class EventHandler(metaclass=ABCMeta):

    def __init__(self):
        self._error_code = 0
        self._message: str = None
        self._data = None
        self._limit = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data: Any):
        self._data = data

    @property
    def error_code(self):
        return self._error_code

    @error_code.setter
    def error_code(self, error_code):
        self._error_code = error_code

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, limit):
        self._limit = limit

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

    @abstractmethod
    def update(self, subject: ApiEvent) -> None:
        pass

    def get_result(self):
        return self.data, self.error_code, self.message
