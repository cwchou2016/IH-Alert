import os
import sys
from os.path import basename

from PySide2 import QtWidgets
from PySide2.QtCore import QThread, Signal, QObject, QCoreApplication, Qt
from time import sleep
from datetime import timedelta, datetime

import alert
from uic import loadUi


class LisFolderHandler(alert.LisFolderHandler, QObject):
    DELETED = Signal(object)

    def __init__(self):
        alert.LisFolderHandler.__init__(self)
        QObject.__init__(self)

    def on_deleted(self, event):
        self.DELETED.emit(event)
        super().on_deleted(event)


class IhFolderHandler(alert.IhFolderHandler, QObject):
    def __init__(self):
        alert.IhFolderHandler.__init__(self)
        QObject.__init__(self)

    def on_modified(self, event):
        super().on_modified(event)


class WatchFolder(QThread):
    WATCHING = Signal(str)
    FINISHED = Signal(str)
    NOTIFY = Signal(str)

    def __init__(self, *, lis_folder, ih_folder):
        super().__init__()
        self._running = False
        self._lis_folder = lis_folder
        self._ih_folder = ih_folder

    def run(self):
        self._running = True
        ob = alert.ObserveCenter()
        lis_handler = LisFolderHandler()
        lis_handler.DELETED.connect(self.on_lis_complete)
        ih_handler = IhFolderHandler()
        ob.schedule(lis_handler, self._lis_folder, False)
        ob.schedule(ih_handler, self._ih_folder, True)
        ob.start()
        while self._running:
            self.WATCHING.emit(f"Running time: {timedelta(seconds=ob.get_run_time())}")
            sleep(1)

        ob.stop()
        ob.join()

        self.FINISHED.emit("Stopped")

    def stop(self):
        self._running = False

    def on_lis_complete(self, event):
        self.NOTIFY.emit(basename(event.src_path))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("mainWindow.ui", self)

        self._watch = WatchFolder(lis_folder="/home/lak/Documents/test", ih_folder=r"/home/lak/Documents/test/Results")
        self._watch.WATCHING.connect(self.update_status_bar)
        self._watch.FINISHED.connect(self.update_event_log)
        self._watch.FINISHED.connect(self.update_status_bar)
        self._watch.NOTIFY.connect(self.update_event_log)

        self.pushButton_start.clicked.connect(self.btn_start_clicked)
        self.pushButton_stop.clicked.connect(self.btn_stop_clicked)

        self.btn_start_clicked()

        self.update()

    def btn_start_clicked(self):
        self.update_status_bar("Starting")
        self._watch.start()
        self.update_event_log("Notification is running")

    def btn_stop_clicked(self):
        self._watch.stop()
        self.update_status_bar("Stopping")

    def update_status_bar(self, msg):
        self.statusBar().showMessage(msg)
        self.update()

    def update_plain_text(self, msg):
        self.plainTextEdit.appendPlainText(msg)
        self.update()

    def update_event_log(self, msg):
        self.update_plain_text(f"{datetime.now()}: {msg}")

    def update(self):
        if self._watch.isRunning():
            self.pushButton_start.hide()
            self.pushButton_stop.show()
        else:
            self.pushButton_start.show()
            self.pushButton_stop.hide()

        super().update()

    def close(self):
        if self._watch.isRunning():
            self._watch.stop()
        super().close()


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
