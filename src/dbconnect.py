import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
import xlrd
import psycopg2

class DBConnect(QWidget):
    def __init__(self, connHandler) -> None:
        super(DBConnect, self).__init__()
        self.initUI()
        self.connHandler = connHandler
        self.initActions()
        self.conn = None

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "dblogin.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)

    def initActions(self):
        self.okBtn.clicked.connect(lambda: self.connHandler(self.connect()))

    def connect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.okBtn.setText("Connect")
        else:
            host = self.host.text()
            db = self.db.text()
            uname = self.uname.text()
            pw = self.pw.text()
            port = self.port.text()
            try:
                self.conn = psycopg2.connect(dbname=db, user=uname, host=host, password=pw, port=port)
                self.conn.set_client_encoding('UTF8')
                self.okBtn.setText("Disconnect")
            except Exception as e:
                print(e)
                self.conn = None
                self.okBtn.setText("Connect")
        return self.conn
