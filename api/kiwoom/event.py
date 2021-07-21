from skogkatt.api import ApiEvent


class DefaultServerEvent(ApiEvent):

    def __init__(self):
        super().__init__()

    def fire_event(self, *args, **kwargs):
        self._data = kwargs
        self._error_code = 0
        self.notify()


class ConnectEvent(ApiEvent):

    def __init__(self):
        super().__init__()

    def fire_event(self, error_code):
        self._data = error_code
        self._error_code = error_code
        self.notify()


class TrDataEvent(ApiEvent):

    def __init__(self):
        super().__init__()

    def fire_event(self, *args, **kwargs):
        self.error_code = 0
        self.data = kwargs
        self.notify()


class OrderSignedEvent(ApiEvent):

    def __init__(self):
        super().__init__()

    def fire_event(self, *args, **kwargs):
        self.error_code = 0
        self.data = kwargs
        self.notify()


class FilterFormulaLoadEvent(ApiEvent):
    def __init__(self):
        super().__init__()

    def fire_event(self, *args, **kwargs):
        self.error_code = 0
        self.data = kwargs
        self.notify()


class ReceiveFilteredEvent(ApiEvent):
    def __init__(self):
        super().__init__()

    def fire_event(self, *args, **kwargs):
        self.error_code = 0
        self.data = kwargs
        self.notify()


class RealTimeDataEvent(ApiEvent):
    def __init__(self):
        super().__init__()

    def fire_event(self, *args, **kwargs):
        self.error_code = 0
        self.data = kwargs
        self.notify()

