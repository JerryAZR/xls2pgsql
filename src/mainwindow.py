import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget
)
from xls2db import Xls2dbPage

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.tabWidget = QTabWidget()
        self.xls2db = Xls2dbPage()
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.addTab(self.xls2db, "XLS2DB")
