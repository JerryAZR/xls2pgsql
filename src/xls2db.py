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
from PyQt5.QtCore import Qt, pyqtSignal
import psycopg2
import pandas as pd
import numpy as np
import traceback
from threading import Thread
from coreutils import get_acronym, sanitize
from colconf import ColConf
from dbconnect import DBConnect
from tablearea import TableArea
from time import sleep # Test only

class Xls2dbPage(QWidget):
    addDataDone = pyqtSignal(int)
    updateProgress = pyqtSignal(int)
    connectDB = pyqtSignal()
    def __init__(self) -> None:
        super(Xls2dbPage, self).__init__()
        self.tableArea = TableArea(self)
        self.initUI()
        self.initActions()
        self.dbDialog = DBConnect(self)
        self.conn = None
        self.sheet = None
        self.err = "" # Placeholder for exceptions on non-UI thread

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "xls2db.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)
        # Set icon
        self.fileBtn.setIcon(QIcon(
            QApplication.style().standardIcon(QStyle.SP_DialogOpenButton)
        ))
        self.previewBtn.setIcon(QIcon(
            QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView)
        ))
        self.verticalLayout.addWidget(self.tableArea)
        self.tableArea.hide()

    def initActions(self):
        self.fileBtn.clicked.connect(self.openExcel)
        self.previewBtn.clicked.connect(self.showExcel)
        self.fnameEdit.textChanged.connect(self.loadExcel)
        self.okBtn.clicked.connect(self.addData)
        self.checkAllBox.stateChanged.connect(self.checkAll)
        self.addDataDone.connect(self.postAdd)
        self.updateProgress.connect(self.progressBar.setValue)

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
            self.sheet = None
            return

        # Clear window
        for i in reversed(range(self.colListLayout.count())): 
            self.colListLayout.itemAt(i).widget().deleteLater()

        # Add columns
        if path.endswith("xls"):
            self.sheet = pd.read_excel(path, engine="xlrd")
        elif path.endswith("xlsx"):
            self.sheet = pd.read_excel(path, engine="openpyxl")
        elif path.endswith("csv"):
            self.sheet = pd.read_csv(path)
        else:
            self.sheet = None
            return
        defaults = []
        colIdx = 0
        for key in self.sheet.dtypes.keys():
            # Get column data type
            if self.sheet.dtypes[key] == np.float64:
                datatype = "NUMBER(16,2)"
            elif self.sheet.dtypes[key] == np.int64:
                datatype = "INTEGER"
            else: # Assume string
                datatype = "VARCHAR(200)"
            # Get column name
            # Avoid duplicate default names
            acronym = sanitize(get_acronym(key))
            if acronym in defaults: # Add a number as suffix
                for suffix in range(2,100): # that should be enough
                    if f"{acronym}{suffix}" not in defaults:
                        # Found a unique name
                        acronym = f"{acronym}{suffix}"
                        break
                # Set text color
                key = f"<font color='red'>{key}</font>"
            defaults.append(acronym)

            # Initialize ColConf object
            newConf = ColConf()
            colIdx += 1
            newConf.setValues(key, acronym, datatype, colIdx)
            self.colListLayout.addWidget(newConf)

    def showExcel(self):
        if self.sheet is None:
            QMessageBox.warning(self, "Path error", "Invalid file path.")
            return
        self.tableArea.setTable(self.sheet)
        self.tableArea.show()

    def addData(self):
        # Check connection
        if self.conn is None:
            # Jump to connection page
            self.connectDB.emit()
            return
        # Create a dict from the column configurations
        colNameDict = {}
        for conf in self.scrollArea.findChildren(ColConf):
            if conf.selected():
                colNameDict[conf.getColDescription()] = conf.getColName()

        # Create table
        self.cur = self.conn.cursor()
        table = sanitize(self.tableNameEdit.text())
        duplicateTable = False
        try:
            self.cur.execute(f"CREATE TABLE {table} (index serial);")
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

        # Add columns
        dataTemplate = ','.join(len(colNameDict) * ["%s"])
        colNames = []
        try:
            for col in self.sheet.columns.values:
                # Get column name
                if col in colNameDict: # Only add the selected columns
                    colName, colType = colNameDict[col]
                    colNames.append(colName)
                    if not duplicateTable:
                        self.cur.execute(f"ALTER TABLE {table} ADD {colName} {colType};")
        except:
            self.conn.rollback()
            QMessageBox.critical(self, "SQL Error", traceback.format_exc())
            return

        # Initialize progress bar
        self.progressBar.setMaximum(self.sheet.shape[0])
        self.progressBar.setValue(0)
        # Disable OK button
        self.okBtn.setEnabled(False)
        # Start thread
        worker = Thread(target=self.addDataWorker,
            args=(colNameDict, table, colNames, dataTemplate))
        worker.start()

    # This function should run in a non-UI thread
    def addDataWorker(self, colNameDict, table, colNames, dataTemplate):
        # Add data
        bufferSize = 1024
        buffer = []
        total = 0
        try:
            for _, row in self.sheet[colNameDict.keys()].iterrows():
                # Construct components (records) of the SQL query using mogrify
                # and add them to a buffer
                # buffer = [(valA1, valA2, ...), (valB1, valB2, ...), ...]
                # It is possible to do this by hand, but mogrify handles
                # missing cell values better
                buffer.append(self.cur.mogrify(f"({dataTemplate})", row.tolist()).decode("utf-8"))
                # check if buffer is full
                if len(buffer) >= bufferSize:
                    # Execute:
                    #   INSERT INTO table_name (col1, col2, ...)
                    #   VALUES (valA1, valA2, ...), (valB1, valB2, ...), ...
                    # The function "executemany" is functionally correct,
                    # but much slower than a single long SQL command
                    self.cur.execute(f"INSERT INTO {table} ({','.join(colNames)}) VALUES {','.join(buffer)};")
                    # Update progress bar and clear buffer
                    total += len(buffer)
                    buffer = []
                    self.updateProgress.emit(total)
            # Add remaining records
            if buffer:
                self.cur.execute(f"INSERT INTO {table} ({','.join(colNames)}) VALUES {','.join(buffer)};")
                total += len(buffer)
                self.updateProgress.emit(total)
            self.addDataDone.emit(total)
        except:
            self.conn.rollback()
            # QMessageBox cannot be displayed in a non-UI thread,
            # so we save the error message here and display it in a message box
            # after execution returns to the UI thread
            self.err = traceback.format_exc()
            self.addDataDone.emit(-1)

    def postAdd(self, returnCode):
        if returnCode < 0:
            QMessageBox.critical(self, "SQL Error", self.err)
        else:
            # Report result
            QMessageBox.information(
                None,
                "Done",
                f"{returnCode} record(s) have been added."
            )
            self.conn.commit()
        # Clean up
        self.cur.close()
        # Re-enable Ok button
        self.okBtn.setEnabled(True)

    def updateConn(self, conn):
        self.conn = conn
