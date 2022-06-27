import sys
from xls2db import Xls2dbPage
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Xls2dbPage()
    main.show()
    sys.exit(app.exec_())
