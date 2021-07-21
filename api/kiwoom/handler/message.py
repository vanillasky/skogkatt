from typing import List


class ServerMessage:
    def __init__(self):
        self.messages = {}

    def update(self, **kwargs) -> None:
        record = {
            'msg': kwargs.get('msg'),
            'rq_name': kwargs.get('rq_name'),
            'tr_code': kwargs.get('tr_code'),
            'screen_no': kwargs.get('screen_no')
        }

        records: List = self.messages.get(kwargs.get('rq_name'), None)
        if records is None:
            records = []

        records.append(record)

    def get_message(self, rq_name: str):
        return self.messages.get(rq_name)

    def pop_message(self, rq_name: str):
        records: List = self.get_message(rq_name)
        if records is None:
            return None

        return records.pop()



