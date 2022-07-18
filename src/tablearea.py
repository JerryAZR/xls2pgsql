import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer

class TableArea(QWidget):
    def __init__(self, parent=None) -> None:
        super(TableArea, self).__init__(parent)
        self.pageIdx = 0
        self.pageSize = 10
        self.initUI()

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "tablearea.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)
        self.tableWidget.setRowCount(self.pageSize)

    def setTable(self, table):
        self.tableWidget.setColumnCount(table.shape[1])
        # Set headers
        for i in range(self.tableWidget.columnCount()):
            self.tableWidget.setHorizontalHeaderItem(
                i, QTableWidgetItem(table.columns.values[i]))
        # Set items
        for c in range(self.tableWidget.columnCount()):
            for r in range(self.pageSize):
                row = self.pageIdx * self.pageSize + r
                if row < table.shape[0]:
                    item = QTableWidgetItem(str(table.iloc[row, c]))
                    self.tableWidget.setItem(r, c, item)
        # self.scheduleResize()
    
    def scheduleResize(self):
        timer = QTimer(self)
        # Give the engine some time to process queued events
        timer.singleShot(10, lambda: self.resize(self.minimumSizeHint()))

