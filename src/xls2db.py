import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
    QFileDialog,
    QApplication,
    QStyle
)
from PyQt5.QtGui import QIcon
import psycopg2
import xlrd
from coreutils import get_acronym, sanitize
from colconf import ColConf
from dbconnect import DBConnect

class Xls2dbPage(QWidget):
    def __init__(self) -> None:
        super(Xls2dbPage, self).__init__()
        self.initUI()
        self.initActions()
        self.dbDialog = DBConnect(self)
        self.conn = None

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
        self.okBtn.clicked.connect(self.addData)

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

        # Clear window
        for i in reversed(range(self.colListLayout.count())): 
            self.colListLayout.itemAt(i).widget().deleteLater()

        # Add columns
        wb = xlrd.open_workbook(path)
        self.sheet = wb.sheet_by_index(0)
        colName = []
        for i in range(self.sheet.ncols):
            # Get column name
            original = self.sheet.cell_value(0, i)
            acronym = sanitize(get_acronym(original))
            # Get column data type
            sample = self.sheet.cell_value(1, i)
            if type(sample) == float:
                datatype = "FLOAT"
            elif type(sample) == int:
                datatype = "INT"
            else: # Assume string
                datatype = "TEXT"

            # Initialize ColConf object
            newConf = ColConf()
            newConf.setValues(original, acronym, datatype)
            self.colListLayout.addWidget(newConf)

    def addData(self):
        # Check connection
        if self.conn is None:
            #TODO: jump to connection page
            return
        # Create a dict from the column configurations
        colNameDict = {}
        for conf in self.scrollArea.findChildren(ColConf):
            if conf.selected():
                colNameDict[conf.getColDescription()] = conf.getColName()

        # Create table
        cur = self.conn.cursor()
        table = sanitize(self.tableNameEdit.text())
        try:
            cur.execute(f"CREATE TABLE {table} (index serial);")
        except psycopg2.errors.DuplicateTable as e:
            print(e)
            self.conn.rollback()
            # Table exists. Ask if the user wants to continue
            response = QMessageBox.question(
                None,
                "Table exists",
                f"Table \"{table}\" already exists. Continue?"
            )
            if response != QMessageBox.Yes:
                return

        # Add columns
        dataTemplate = ','.join(len(colNameDict) * ["%s"])
        colNames = []
        for i in range(self.sheet.ncols):
            # Get column name
            col = self.sheet.cell_value(0, i)
            if col in colNameDict: # Only add the selected columns
                colName, colType = colNameDict[col]
                colNames.append(colName)
                try:
                    cur.execute(f"ALTER TABLE {table} ADD {colName} {colType};")
                except psycopg2.errors.DuplicateColumn as e:
                    print(e)
                    self.conn.rollback()
                    # TODO: Ask user what to do with duplicate column

        # Add data
        for i in range(1, self.sheet.nrows):
            dataArray = []
            for j in range(self.sheet.ncols):
                col = self.sheet.cell_value(0, j)
                if col in colNameDict: # Only add the selected columns
                    data = self.sheet.cell_value(i, j)
                    dataArray.append(data)
            cur.execute(
                f"INSERT INTO {table} ({','.join(colNames)}) VALUES ({dataTemplate})",
                dataArray)

        # Report result
        num_records = self.sheet.nrows - 1
        QMessageBox.information(
            None,
            "Done",
            f"{num_records} record(s) have been added."
        )
        self.conn.commit()
        cur.close()

    def updateConn(self, conn):
        self.conn = conn
