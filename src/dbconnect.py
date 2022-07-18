import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtGui import QIcon
import xlrd
import psycopg2
import json
import traceback

class DBConnect(QWidget):
    def __init__(self, connHandler) -> None:
        super(DBConnect, self).__init__()
        self.initUI()
        self.connHandler = connHandler
        self.initActions()
        self.conn = None
        self.jsonfile = "history.json"
        self.history = {}
        self.load()

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "dblogin.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)
        # Load greed circle
        GreenIconFile = "green.svg"
        GreenIconPath = os.path.join(myPath, "ui", GreenIconFile)
        self.greenIcon = QIcon(GreenIconPath).pixmap(20, 20)
        # Load red circle
        RedIconFile = "red.svg"
        RedIconPath = os.path.join(myPath, "ui", RedIconFile)
        self.redIcon = QIcon(RedIconPath).pixmap(20, 20)
        self.indicator.setPixmap(self.redIcon)

    def initActions(self):
        self.okBtn.clicked.connect(lambda: self.connHandler(self.connect()))
        self.saveBtn.clicked.connect(self.save)
        self.comboBox.currentIndexChanged.connect(self.autofill)

    def connect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.okBtn.setText("Connect")
            # Update indicator and status label
            self.indicator.setPixmap(self.redIcon)
            self.statusLabel.setText("Not connected.")
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
                # Update indicator and status label
                self.indicator.setPixmap(self.greenIcon)
                self.statusLabel.setText(f"Connected to DB \"{db}\" at {host}")
            except Exception as e:
                QMessageBox.warning(self, "Failed to Connect", str(e))
                self.conn = None
                self.okBtn.setText("Connect")
        return self.conn

    
    def save(self):
        # Save log in info to a json file
        host = self.host.text()
        db = self.db.text()
        uname = self.uname.text()
        # pw = self.pw.text()
        port = self.port.text()
        name = self.profileName.text()

        # Create JSON entry
        jentry = {
            "host": host,
            "port": port,
            "uname": uname,
            "db": db
        }
        # Auto generate name if none provided
        if name == "":
            name = f"{uname}@{host}:{port}"
        # TODO: warn user on overwrite
        self.history[name] = jentry
        with open(self.jsonfile, "w") as out_file:
            json.dump(self.history, out_file, indent=4)
        # Reload selections
        self.load()
        # Restore everything
        self.comboBox.setCurrentIndex(self.comboBox.findText(name))

    
    def load(self):
        # Load history from json file
        try:
            with open(self.jsonfile, "r") as in_file:
                self.history = json.load(in_file)
        except FileNotFoundError:
            self.history = {}
        self.comboBox.clear()
        for key in self.history:
            self.comboBox.addItem(key)
        
    def autofill(self, index):
        # using try-except because this function could fail when reloading
        try:
            entryName = self.comboBox.currentText()
            if entryName in self.history:
                entry = self.history[entryName]
            else:
                entry = None
                return

            # jentry = {
            #             "host": host,
            #             "port": port,
            #             "user": uname,
            #             "db": db
            #         }
            self.profileName.setText(entryName)
            self.host.setText(entry["host"])
            self.db.setText(entry["db"])
            self.uname.setText(entry["uname"])
            self.port.setText(entry["port"])
            
        except Exception:
            traceback.print_exc()
