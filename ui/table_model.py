import math

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from numpy import int32, int64

from skogkatt.commons.util.numeral import format_with


class DataframeTableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.apply_display_role(index)

        if role == Qt.TextAlignmentRole:
            return self.apply_alignment_role(index)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])

    def apply_display_role(self, item):
        value = self._data.iloc[item.row(), item.column()]
        # print(value, type(value))
        if isinstance(value, int) or isinstance(value, int32) or isinstance(value, int64):
            return format_with(value)

        if isinstance(value, float):
            if math.isnan(value):
                return ""

            value = "{:.2f}".format(value)
            formatted = format_with(value)
            if formatted.endswith(".0"):
                formatted = formatted.split(".")[0]

            return formatted

        return str(value)

    def apply_alignment_role(self, item):
        value = self._data.iloc[item.row(), item.column()]

        if isinstance(value, int) or isinstance(value, float) or isinstance(value, int32) or isinstance(value, int64):
            # Align right, vertical middle.
            return Qt.AlignVCenter + Qt.AlignRight

        return Qt.AlignBottom + Qt.AlignCenter

    # def sort(self, col, order):
    #     """Sort table by given column number."""
    #     self.layoutAboutToBeChanged.emit()
    #     self._data = self._data.sort_values(self._data.columns[col], ascending=order == Qt.AscendingOrder)
    #     self.layoutChanged.emit()
