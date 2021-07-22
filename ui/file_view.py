import os
import re
import sys

from PyQt5.QtCore import QSize, Qt, pyqtSlot, QRect
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QBrush, QColor, QPixmap, QPainter, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QApplication, QGridLayout, \
    QLabel, QPushButton, QLineEdit, QCheckBox, QPlainTextEdit, QMdiSubWindow


class FileViewWindow(QMdiSubWindow):
    def __init__(self):
        QMdiSubWindow.__init__(self)
        self.last_match = None
        self.cursor = None
        self.current_index = -1
        self.matched_list = []

        win_icon = QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), "icons/document_file_icon_64px.png")))
        self.setWindowIcon(win_icon)

        vbox: QVBoxLayout = QVBoxLayout()
        grid_layout: QGridLayout = QGridLayout()

        # Search Box
        self.lb_prev = QLabel()
        self.lb_next = QLabel()
        self.le_find = QLineEdit()
        self.lb_result = QLabel('0 results')
        self.chk_whole_word = QCheckBox('Whole Words')
        self.chk_case_sensitive = QCheckBox('Case Sensitive')
        self.pb_find = QPushButton('Find')
        self.init_search_box(grid_layout)

        # TextEdit
        self.edit = LineNumberTextEdit()
        self.edit.setReadOnly(True)
        font = QFont("Courier New", 9)
        self.edit.setFont(font)

        self.set_ui_event()
        self.found_text_format = QTextCharFormat()
        self.found_text_format.setBackground(QBrush(QColor("yellow")))

        vbox.addLayout(grid_layout)
        vbox.addWidget(self.edit)

        widget = QWidget()
        widget.setLayout(vbox)
        self.setWidget(widget)

    def init_search_box(self, layout: QGridLayout):
        self.init_prev_next_button()
        layout.addWidget(self.le_find, 0, 0)
        layout.addWidget(self.lb_result, 0, 1)
        layout.addWidget(self.lb_prev, 0, 2)
        layout.addWidget(self.lb_next, 0, 3)
        layout.addWidget(self.chk_whole_word, 0, 4)
        layout.addWidget(self.chk_case_sensitive, 0, 5)
        layout.addWidget(self.pb_find, 0, 6)

    def init_prev_next_button(self):
        btn_next = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons/down_c_arrow_icon_64px.png"))
        btn_prev = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons/up_arrow_icon_64px.png"))

        pixmap_prev = QPixmap(btn_prev)
        pixmap_prev = pixmap_prev.scaled(16, 16)

        pixmap_next = QPixmap(btn_next)
        pixmap_next = pixmap_next.scaled(16, 16)

        self.lb_prev.setPixmap(pixmap_prev)
        self.lb_next.setPixmap(pixmap_next)

    def set_ui_event(self):
        self.le_find.returnPressed.connect(self.find_all)
        self.pb_find.clicked.connect(self.find_all)
        self.lb_prev.mousePressEvent = self.goto_prev
        self.lb_next.mousePressEvent = self.goto_next

    def goto_matched(self, index_offset: int):
        index = self.current_index + index_offset
        self.move_cursor(self.matched_list[index])
        self.edit.setTextCursor(self.cursor)
        self.current_index = index
        self.update_count(self.current_index)

    def goto_prev(self, event):
        if self.current_index > 0:
            self.goto_matched(-1)

    def goto_next(self, event):
        if self.current_index < len(self.matched_list) - 1:
            self.goto_matched(1)

    def set_file(self, filepath):
        self.setWindowTitle(filepath)
        with open(filepath, 'r', encoding='utf-8') as file:
            data = file.read()
            self.edit.setPlainText(data)

    def clear_cursor(self):
        if self.cursor is None:
            return

        cursor = self.edit.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()
        self.edit.setTextCursor(cursor)

    def find_all(self):
        self.last_match = None
        self.matched_list = []
        self.update_count()
        self.clear_cursor()

        text = self.edit.toPlainText()
        query = self.le_find.text()

        if self.chk_whole_word.isChecked():
            query = rf'\W{query}\W'

        flags = 0 if self.chk_case_sensitive.isChecked() else re.I
        pattern = re.compile(query, flags)

        self.cursor = self.edit.textCursor()

        # If the last match was successful, start at position after the last
        # match's start, else at 0
        start = self.last_match.start() + 1 if self.last_match else 0

        self.last_match = pattern.search(text, start)
        while self.last_match:
            self.matched_list.append(self.last_match)
            start = self.last_match.start()
            end = self.last_match.end()

            # If 'Whole words' is checked, the selection would include the two
            # non-alphanumeric characters we included in the search, which need
            # to be removed before marking them.
            if self.chk_whole_word.isChecked():
                start += 1
                end -= 1

            self.move_cursor(self.last_match)
            self.highlight(self.found_text_format)
            self.last_match = pattern.search(text, end)

        if len(self.matched_list) > 0:
            self.current_index = 0
            self.update_count(self.current_index)
            self.move_cursor(self.matched_list[0])
            self.edit.setTextCursor(self.cursor)
            # self.highlight(self.current_text_format)

    def update_count(self, index=None):
        if index is None:
            self.lb_result.setText('0 results')
        else:
            self.lb_result.setText(f'{index+1} / {str(len(self.matched_list))}')

    def highlight(self, text_char_format):
        self.cursor.mergeCharFormat(text_char_format)

    def move_cursor(self, match):
        self.cursor.setPosition(match.start())
        self.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, match.end() - match.start())

    # def update_line_numbers(self):
    #     self.ui.text_edit.setViewportMargins(80, 0, 0, 0)


class LineNumberTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        self.line_number_width = 50
        self.line_number_area = LineNumberArea(self)
        self.setViewportMargins(self.line_number_width, 0, 0, 0)
        # self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        # self.update_line_number_area_width(0)

    @pyqtSlot()
    def highlight_current_line(self):
        extra_selections = []
        selection = QTextEdit.ExtraSelection()
        line_color = QColor(Qt.blue).lighter(160)
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    @pyqtSlot(QRect, int)
    def update_line_number_area(self, rect: QRect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_width, rect.height())

        # if rect.contains(self.viewport().rect()):
        #     self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_width, cr.height()))

    # @pyqtSlot(int)
    # def update_line_number_area_width(self, new_block_count):
    #     self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def line_number_area_width(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(5, int(top), self.line_number_width, self.fontMetrics().height(), Qt.AlignLeft, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


class LineNumberArea(QWidget):
    def __init__(self, editor):
        QWidget.__init__(self, parent=editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = FileViewWindow()
    win.show()
    app.exec_()
