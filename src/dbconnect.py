import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
import xlrd
import psycopg2

class DBConnect(QDialog):
    def __init__(self, parent) -> None:
        super(DBConnect, self).__init__(parent)
        self.initUI()

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "dblogin.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)

    def connect(self):
        host = self.host.text()
        db = self.db.text()
        uname = self.uname.text()
        pw = self.pw.text()
        try:
            conn = psycopg2.connect(dbname=db, user=uname, host=host, password=pw)
            conn.set_client_encoding('UTF8')
            return conn
        except Exception as e:
            print(e)
            return None
