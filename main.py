import sys

from PyQt5 import QtWidgets, uic


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mainWindow.ui", self)

        self.pushButton_start.clicked.connect(self.btn_start_clicked)
        self.pushButton_stop.clicked.connect(self.btn_stop_clicked)

        self.update()

    def btn_start_clicked(self):
        self.update_status_bar("start clicked")
        self.update_plain_text("start clicked")

    def btn_stop_clicked(self):
        self.update_status_bar("stop clicked")
        self.update_plain_text("stop clicked")

    def update_status_bar(self, msg):
        self.statusBar().showMessage(msg)
        self.update()

    def update_plain_text(self, msg):
        self.plainTextEdit.appendPlainText(msg)
        self.update()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
