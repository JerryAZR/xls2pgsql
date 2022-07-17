import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor
from coreutils import sanitize

class ColConf(QWidget):
    ID = 0
    COLORS = [QColor(220, 220, 220), QColor(180, 180, 180)]

    def __init__(self) -> None:
        super(ColConf, self).__init__()
        self.initUI()
        self.initActions()

    def initUI(self):
        # Load the Qt ui (xml) file
        myPath = os.path.dirname(__file__)
        uiFile = "columnconf.ui"
        uic.loadUi(os.path.join(myPath, "ui", uiFile), self)
        self.checkBox.setCheckState(True)
        self.checkBox.setTristate(False)

        palette = QPalette()
        palette.setColor(QPalette.Window, ColConf.COLORS[ColConf.ID])
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        ColConf.ID = (ColConf.ID + 1) & 1

    def initActions(self):
        self.checkBox.stateChanged.connect(self.toggleState)

    def setValues(self, description, name, datatype, idx):
        self.description.setText(description)
        self.name.setText(name)
        self.dataType.setCurrentText(datatype)
        self.idxLabel.setText(str(idx))

    def toggleState(self, state):
        self.name.setEnabled(state)
        self.dataType.setEnabled(state)
        self.description.setEnabled(state)
        self.idxLabel.setEnabled(state)

    def selected(self) -> bool:
        return self.checkBox.isChecked()

    def setSelected(self, state: bool) -> None:
        self.checkBox.setCheckState(state)

    def getColName(self):
        return (sanitize(self.name.text()), sanitize(self.dataType.currentText()))

    def getColDescription(self):
        return self.description.text()
