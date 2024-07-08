import sys
from PyQt5.QtWidgets import QApplication
from cbz_reader import CBZReader

if __name__ == '__main__':
    app = QApplication(sys.argv)
    reader = CBZReader()
    reader.show()
    sys.exit(app.exec_())
