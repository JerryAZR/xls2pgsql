import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
    QProgressDialog,
    QFileDialog,
    QApplication,
    QStyle
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import psycopg2
import pandas as pd
import numpy as np
import traceback
from coreutils import get_acronym, sanitize
from colconf import ColConf
from dbconnect import DBConnect
from time import sleep # Test only

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
        self.checkAllBox.stateChanged.connect(self.checkAll)

    def checkAll(self, state):
        for conf in self.scrollArea.findChildren(ColConf):
            conf.setSelected(state)

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
        self.sheet = pd.read_excel(path)
        defaults = []
        for key in self.sheet.dtypes.keys():
            # Get column name
            # Avoid duplicate default names
            acronym = sanitize(get_acronym(key))
            if acronym in defaults: # Add a number as suffix
                for suffix in range(2,100): # that should be enough
                    if f"{acronym}{suffix}" not in defaults:
                        # Found a unique name
                        acronym = f"{acronym}{suffix}"
                        break
            defaults.append(acronym)
            # Get column data type
            if self.sheet.dtypes[key] == np.float64:
                datatype = "FLOAT"
            elif self.sheet.dtypes[key] == np.int64:
                datatype = "INT"
            else: # Assume string
                datatype = "TEXT"

            # Initialize ColConf object
            newConf = ColConf()
            newConf.setValues(key, acronym, datatype)
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
        duplicateTable = False
        try:
            cur.execute(f"CREATE TABLE {table} (index serial);")
        except psycopg2.errors.DuplicateTable:
            duplicateTable = True
            self.conn.rollback()
            # Table exists. Ask if the user wants to continue
            response = QMessageBox.question(
                None,
                "Table exists",
                f"Table \"{table}\" already exists. Continue?"
            )
            if response != QMessageBox.Yes:
                return

        # Disable OK button
        self.okBtn.setEnabled(False)

        # Add columns
        dataTemplate = ','.join(len(colNameDict) * ["%s"])
        colNames = []
        for col in self.sheet.columns.values:
            # Get column name
            if col in colNameDict: # Only add the selected columns
                colName, colType = colNameDict[col]
                colNames.append(colName)
                if not duplicateTable:
                    cur.execute(f"ALTER TABLE {table} ADD {colName} {colType};")

        # Add data
        self.progressBar.setMaximum(self.sheet.shape[0])
        self.progressBar.setValue(0)
        bufferSize = 16
        buffer = []
        total = 0
        for _, row in self.sheet[colNameDict.keys()].iterrows():
            # check if buffer is full
            buffer.append(row.tolist())
            if len(buffer) >= bufferSize:
                try:
                    cur.executemany(
                        f"INSERT INTO {table} ({','.join(colNames)}) VALUES ({dataTemplate})",
                        buffer)
                except:
                    QMessageBox.critical(self, "SQL Error", traceback.format_exc())
                    self.conn.rollback()
                    self.okBtn.setEnabled(True)
                    return
                # Update progress bar and clear buffer
                total += len(buffer)
                buffer = []
                self.progressBar.setValue(total)
        # Add remaining records
        if buffer:
            cur.executemany(
                f"INSERT INTO {table} ({','.join(colNames)}) VALUES ({dataTemplate})",
                buffer)
            total += len(buffer)
            self.progressBar.setValue(total)

        # Report result
        QMessageBox.information(
            None,
            "Done",
            f"{total} record(s) have been added."
        )
        self.conn.commit()
        cur.close()
        # Re-enable Ok button
        self.okBtn.setEnabled(True)

    def updateConn(self, conn):
        self.conn = conn
