class Ticker:

    __slots__ = {'code', 'name', 'acc_date', 'ipo_date', 'market', 'industry', 'corp_code'}

    def __init__(self, code, name, corp_code, acc_date, ipo_date, market, industry):
        super(Ticker, self).__setattr__('code', code)
        super(Ticker, self).__setattr__('name', name)
        super(Ticker, self).__setattr__('acc_date', acc_date)
        super(Ticker, self).__setattr__('ipo_date', ipo_date)
        super(Ticker, self).__setattr__('market', market)
        super(Ticker, self).__setattr__('industry', industry)
        super(Ticker, self).__setattr__('corp_code', corp_code)

    def __setattr__(self, *args):
        raise TypeError('Ticker cannot be modified')

    def __delattr__(self, *args):
        raise TypeError('Ticker properties cannot be deleted')

    def __str__(self):
        string_value = '{code:' + str(self.code) \
            + ', name:' + str(self.name) \
            + ', acc_date' + str(self.acc_date) \
            + ', ipo_date:' + str(self.ipo_date) \
            + ', market:' + str(self.market) \
            + ', industry:' + str(self.industry) \
            + ', corp_code:' + str(self.corp_code) + '}'

        return string_value

    @staticmethod
    def from_dict(dic):
        return Ticker(dic['code'],
                      dic['name'],
                      dic['corp_code'],
                      dic['acc_date'],
                      dic['ipo_date'],
                      dic['market'],
                      dic['industry'])

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "acc_date": self.acc_date,
            "ipo_date": self.ipo_date,
            "market": self.market,
            "industry": self.industry,
            "corp_code": self.corp_code
        }


