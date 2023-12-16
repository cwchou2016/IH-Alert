import sys
from os.path import basename

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from time import sleep
from datetime import timedelta

import alert


class FileHandler(alert.FileEventHandler, QObject):
    DELETED = pyqtSignal(object)

    def __init__(self):
        alert.FileEventHandler.__init__(self)
        QObject.__init__(self)

    def on_deleted(self, event):
        super().on_deleted(event)
        self.DELETED.emit(event)


class WatchFolder(QThread):
    WATCHING = pyqtSignal(str)
    FINISHED = pyqtSignal(str)
    NOTIFY = pyqtSignal(str)

    def __init__(self, folder_path, alert_sound):
        super().__init__()
        self._running = False
        self._folder = folder_path
        self._alert = alert_sound

    def run(self):
        self._running = True
        ob = alert.ObserveCenter()
        handler = FileHandler()
        handler.set_sound(self._alert)
        handler.DELETED.connect(self.emit_notification)
        ob.schedule(handler, self._folder, True)
        ob.start()
        while self._running:
            self.WATCHING.emit(f"Running time: {timedelta(seconds=ob.get_run_time())}")
            sleep(1)

        ob.stop()
        ob.join()

        self.FINISHED.emit("finished")

    def stop(self):
        self._running = False

    def emit_notification(self, event):
        self.NOTIFY.emit(basename(event.src_path))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mainWindow.ui", self)

        self._watch = WatchFolder("/home/lak/Documents/test", "10-seconds-loop-2-97528.mp3")
        self._watch.WATCHING.connect(self.update_status_bar)
        self._watch.FINISHED.connect(self.update_plain_text)
        self._watch.NOTIFY.connect(self.update_plain_text)

        self.pushButton_start.clicked.connect(self.btn_start_clicked)
        self.pushButton_stop.clicked.connect(self.btn_stop_clicked)

        self.update()

    def btn_start_clicked(self):
        self.update_status_bar("start clicked")
        self._watch.start()
        self.update_plain_text("start clicked")

    def btn_stop_clicked(self):
        self._watch.stop()
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
