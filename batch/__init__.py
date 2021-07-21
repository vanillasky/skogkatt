class BatchStatus:
    """
    배치 상태
    status - 1:시작, 0: 정상종료, 음수: 에러발생
    """
    def __init__(self, name, start, end=None, elapsed=None, status=1, trace=None):
        self.name = name
        self.start = start
        self.end = end
        self.status = status
        self.elapsed = elapsed
        self.trace = trace

    def __str__(self):
        string_value = 'BatchStatus {name:' + str(self.name) \
            + ', start:' + str(self.start) \
            + ', end:' + str(self.end) \
            + ', elapsed:' + str(self.elapsed) \
            + ', status:' + str(self.status) + '}'

        return string_value

    def to_dict(self):
        return {'name': self.name,
                'start': self.start,
                'end': self.end,
                'elapsed': str(self.elapsed),
                'status': self.status,
                'trace': self.trace}

    @staticmethod
    def from_dict(dic):
        return BatchStatus(dic['name'], dic['start'], dic['end'], dic['elapsed'], dic['status'], dic['trace'])


