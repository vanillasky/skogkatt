
class CrawlerError(RuntimeError):
    def __init__(self, err_msg='An error occurred while running crawler', **kwargs):
        super().__init__(err_msg, kwargs)
        self.message = err_msg
        self.stock_code = kwargs.get('stock_code', None)
        self.industry = kwargs.get('industry', None)
        self.corp_name = kwargs.get('corp_name', None)


class PricerError(ValueError):
    def __init__(self, err_msg='An error occurred while estimate price', **kwargs):
        super().__init__(err_msg, kwargs)
        self.message = err_msg
        self.stock_code = kwargs.get('stock_code', None)
        self.industry = kwargs.get('industry', None)
        self.corp_name = kwargs.get('corp_name', None)


class StatementParseError(RuntimeError):
    def __init__(self, err_msg='An error occurred while parsing financial data', **kwargs):
        super().__init__(err_msg, kwargs)
        self.message = err_msg
        self.stock_code = kwargs.get('stock_code', None)
        self.industry = kwargs.get('industry', None)
        self.corp_name = kwargs.get('corp_name', None)


class NoDataFoundError(ValueError):
    def __init__(self, err_msg='No data found'):
        super().__init__(err_msg)


class PriceRevisedWarning(ValueError):
    def __init__(self, err_msg='Adjusted stock price detected. ', **kwargs):
        super().__init__(err_msg)
        self.stock_code = kwargs.get('stock_code', None)
        self.corp_name = kwargs.get('corp_name', None)
