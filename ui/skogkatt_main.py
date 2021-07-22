import sys

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QDockWidget, QListWidget, QMdiSubWindow, QTextEdit
from PyQt5 import uic

from skogkatt.ui.dashboard import DashboardView
from skogkatt.ui.file_view import FileViewWindow

""" Do not remove import res_rc"""
import res_rc


class MainWindow(QMainWindow):

    count = 0

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = uic.loadUi("skogkatt_main.ui")
        self.set_ui_event()
        self.ui.show()
        self.file_view = None
        self.dashboard_view = None
        self.screener = None

        self.list_widget = QListWidget()

        self.list_widget.addItem("Google")

        self.ui.dock_widget.setWindowTitle("Dock Test")
        self.ui.dock_widget.setWidget(self.list_widget)
        self.ui.dock_widget.setFloating(False)
        # self.addDockWidget(Qt.BottomDockWidgetArea, self.ui.dock_widget)

    def set_ui_event(self):
        self.ui.actionS_RIM_Wizard.triggered.connect(self.onclick_test)
        self.ui.action_open.triggered.connect(self.open_file)
        self.ui.action_batch_status.triggered.connect(self.open_batch_dashboard)
        self.ui.action_screener.triggered.connect(self.open_screener)

    def open_batch_dashboard(self):
        if self.dashboard_view is not None and self.dashboard_view.isVisible():
            return
        MainWindow.count = MainWindow.count + 1

        self.dashboard_view = DashboardView()
        self.ui.mdi_area.addSubWindow(self.dashboard_view)
        self.dashboard_view.showMaximized()

    def open_file(self):
        path = QFileDialog.getOpenFileName(self, 'Open File', '../../logs')
        if path != ('', ''):
            self.open_file_view_window(path[0])

    def open_file_view_window(self, filepath):
        MainWindow.count = MainWindow.count + 1

        self.file_view = FileViewWindow()
        self.file_view.set_file(filepath)
        self.ui.mdi_area.addSubWindow(self.file_view)
        self.file_view.showMaximized()

    def open_screener(self):
        MainWindow.count = MainWindow.count + 1
        self.ui.mdi_area.addSubWindow(self.ui.subwindow)
        self.ui.subwindow.showMaximized()
        # self.screener = ScreenerView()



    def onclick_test(self):
        print("sdsdfsdf")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    # win.show()
    app.exec_()
