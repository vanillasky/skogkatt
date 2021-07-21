from typing import List

from skogkatt.api.kiwoom.event import ApiEvent
from skogkatt.api import EventHandler


class FilterFormula:

    def __init__(self, index, name):
        self._index = index
        self._name = name
        self._items = []

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._name

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items

    def __str__(self):
        items = [item for item in self.items]

        string_value = 'FilterFormula - ' \
                       'index: {self.index}, ' \
                       'name: {self.name}, ' \
                       .format(self=self)
        return string_value + 'items[ ' + ','.join(items) + ']'


class FormulaLoadEventHandler(EventHandler):
    """
    조건검색 로드 이벤트 처리.
    이벤트로 부터 인덱스^조검검색명 리스트를 받아서 각각의 Condition 객체를
    리스트에 담아서 반환한다.
    """
    def __init__(self,):
        super().__init__()
        self.conditions: List[FilterFormula] = []

    def update(self, event: ApiEvent) -> None:
        cond_list = event.data.get('conditions')
        for cond in cond_list:
            code = cond.split('^')
            if len(code) > 0:
                condition = FilterFormula(code[0], code[1])
                self.conditions.append(condition)

    def get_result(self) -> dict:
        return {'data': self.conditions, 'error': None}


class ConditionalStockHandler(EventHandler):
    def __init__(self,):
        super().__init__()
        self.condition: FilterFormula = None

    def update(self, event: ApiEvent) -> None:
        stock_codes_str = event.data.get('code_list')
        codes = stock_codes_str.split(';')[:-1]

        self.condition = FilterFormula(event.data.get('cond_index'), event.data.get('cond_name'))
        self.condition.items = codes

    def get_result(self) -> dict:
        return {'data': self.condition, 'error': None}
