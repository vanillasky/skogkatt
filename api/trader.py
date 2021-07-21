from datetime import datetime


class Trader:

    MARKET_OPEN = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 9, 00)
    MARKET_CLOSE = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 15, 30)

    @staticmethod
    def is_market_opened():
        """ 주문가능 시각 확인.
        토요일, 일요일 -> False
        9시 이전, 15시 30분 이후 -> False
        공휴일, 장시간 연장 등을 확인 안함
        """
        day_of_week = datetime.today().weekday()
        if day_of_week > 4:
            return False

        current = datetime.now()
        if Trader.MARKET_OPEN < current < Trader.MARKET_CLOSE:
            return True
        else:
            return False

    def __init__(self):
        pass
