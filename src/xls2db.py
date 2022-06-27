import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QApplication,
    QStyle
)
from PyQt5.QtGui import QIcon
import xlrd
from pypinyin import Style, lazy_pinyin
import re

class Xls2dbPage(QMainWindow):
    def __init__(self) -> None:
        super(Xls2dbPage, self).__init__()
        self.initUI()
        self.initActions()

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "xls2db.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)
        # Set icon
        self.fileBtn.setIcon(QIcon(
            QApplication.style().standardIcon(QStyle.SP_DialogOpenButton))
        )

    def initActions(self):
        self.fileBtn.clicked.connect(self.openExcel)
        self.fnameEdit.textChanged.connect(self.loadExcel)

    def openExcel(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            None,
            "MS Excel (*.xls *.xlsx);;All Files (*)")
        if fname is None:
            return
        self.fnameEdit.setText(fname) # triggers the loadExcel function

    def loadExcel(self):
        path = self.fnameEdit.text()
        # Get default table name
        fullName = path.split('/')[-1]
        defaultName = sanitize(get_acronym(fullName.split('.')[0]))
        self.tableNameEdit.setText(defaultName)

        # Return if file does not exist
        if not os.path.exists(path):
            return


def get_acronym(raw):
    return ''.join(lazy_pinyin(raw, style=Style.FIRST_LETTER))

def sanitize(raw):
    # Only keey alphanumeric chars
    return re.sub(r"[^a-zA-Z0-9]", "", raw)
