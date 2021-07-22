import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMdiSubWindow, QVBoxLayout, QWidget, QTableView, QStyle
from tabulate import tabulate

# from skogkatt.fs.dao import UnresolvedTickerDao
from skogkatt.ui.table_model import DataframeTableModel


class DashboardView(QMdiSubWindow):
    def __init__(self):
        QMdiSubWindow.__init__(self)
        win_icon = QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), "icons/board_icon_64px.png")))
        self.setWindowIcon(win_icon)
        self.setWindowTitle("Dashboard")

        outer_vbox: QVBoxLayout = QVBoxLayout()

        self.tv_error_ticker = QTableView()
        # style = QStyle("{background-color: yellow}")
        self.paint_error_ticker_table()

        outer_vbox.addWidget(self.tv_error_ticker)
        widget = QWidget()
        widget.setLayout(outer_vbox)
        self.setWidget(widget)

    # def paint_error_ticker_table(self):
    #     dao = UnresolvedTickerDao()
    #     df = dao.find(as_dataframe=True)
    #     df.columns = ['종목코드', '종목명', '결산월', '상장일자', '시장(S:코스피, K:코스닥)', '업종', '작업']
    #     model = DataframeTableModel(df)
    #     self.tv_error_ticker.setModel(model)
    #     self.tv_error_ticker.horizontalHeader().setStyleSheet("::section{background-color: yellow}")
    #     self.tv_error_ticker.resizeColumnsToContents()
    #     # self.tv_error_ticker.setSortingEnabled(True)
