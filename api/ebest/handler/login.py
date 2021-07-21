from skogkatt.api import EventHandler, ApiEvent


class LoginEventHandler(EventHandler):
    """
    API의 connect 메소드 호출 후 발생하는 이벤트 처리
    :param err_code: 0 - 접속성공 else 접속실패
    :param login_time: 접속 시각
    :return: 접속 성공시 {'data': 0, 'err_message': None}
             접속 실패시 {'data': error_code, 'err_message': 'API 접속 실패'}
    """
    def __init__(self):
        super().__init__()

    def update(self, event: ApiEvent) -> None:
        if event.error_code > 0:
            self._message = event.message
            self._error_code = event.error_code
            self._data = None
        else:
            self._data = 0
            self._error_code = 0

