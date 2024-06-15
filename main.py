import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QThread, Signal, QCoreApplication, Qt
from time import sleep
from datetime import timedelta, datetime

from PySide6.QtWidgets import QFileDialog

import alert
from settings import Settings
from uic import loadUi


class WatchFolder(QThread):
    WATCHING = Signal(str)
    FINISHED = Signal(str)
    NOTIFY = Signal(str)

    def __init__(self, config):
        super().__init__()
        self._running = False
        self._config = config

    def run(self):
        self._running = True
        ob = alert.ObserveCenter()
        lis_handler = alert.LisFolderHandler(audio_file=self._config.get("complete_sound"), delay=0)
        lis_handler.DELETED.connect(self.on_lis_complete)
        ih_handler = alert.IhFolderHandler(audio_file=self._config.get("alert_sound"), delay=60)
        ih_handler.RECEIVED.connect(self.on_received)
        ih_handler.CONFIRMED.connect(self.on_confirmed)
        ob.schedule(lis_handler, self._config.get("lis_folder"), False)
        ob.schedule(ih_handler, self._config.get("ih_folder"), True)
        ob.start()
        while self._running:
            self.WATCHING.emit(f"Running time: {timedelta(seconds=ob.get_run_time())}")
            sleep(1)

        ob.stop()
        ob.join()

        self.FINISHED.emit("Stopped")

    def stop(self):
        self._running = False

    def on_lis_complete(self, sample):
        self.NOTIFY.emit(f"{sample.sample_id} is completed")

    def on_received(self, sample):
        self.NOTIFY.emit(f"{sample.sample_id} is received")

    def on_confirmed(self, sample):
        self.NOTIFY.emit(f"{sample.sample_id} is confirmed")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("mainWindow.ui", self)

        self._watch = None

        self.pushButton_start.clicked.connect(self.btn_start_clicked)
        self.pushButton_stop.clicked.connect(self.btn_stop_clicked)
        self.actionSettings.triggered.connect(self.show_setting)

        self.btn_start_clicked()

        self.update()

    def show_setting(self):
        self.btn_stop_clicked()
        widget = SettingWindow()
        widget.CLOSE.connect(self.btn_start_clicked)
        widget.show()

    def btn_start_clicked(self):
        self.update_status_bar("Starting")
        if self._watch is not None:
            self.btn_stop_clicked()

        config = Settings("config.ini")
        self._watch = WatchFolder(config)
        self._watch.WATCHING.connect(self.update_status_bar)
        self._watch.FINISHED.connect(self.update_event_log)
        self._watch.FINISHED.connect(self.update_status_bar)
        self._watch.NOTIFY.connect(self.update_event_log)
        self._watch.start()
        self.update_event_log("Notification is running")

    def btn_stop_clicked(self):
        if self._watch is None:
            return

        self._watch.stop()
        self.update_status_bar("Stopping")

    def update_status_bar(self, msg):
        self.statusBar().showMessage(msg)
        self.update()

    def update_plain_text(self, msg):
        self.plainTextEdit.appendPlainText(msg)
        self.update()

    def update_event_log(self, msg):
        self.update_plain_text(f"{datetime.now()}:  {msg}")

    def update(self):
        if self._watch is None:
            pass
        elif self._watch.isRunning():
            self.pushButton_start.hide()
            self.pushButton_stop.show()
        else:
            self.pushButton_start.show()
            self.pushButton_stop.hide()

        super().update()

    def closeEvent(self, event):
        if self._watch.isRunning():
            self._watch.stop()
            self._watch.wait()
        super().closeEvent(event)


class SettingWindow(QtWidgets.QWidget):
    CLOSE = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("settings.ui", self)

        self.times = [TimeEdit(self) for _ in range(3)]
        layout = QtWidgets.QHBoxLayout(self.time_widget)
        for te in self.times:
            layout.addWidget(te)

        self._settings = {
            "ih_folder": self.lineIhFolder,
            "lis_folder": self.lineLisFolder,
            "complete_sound": self.lineCompleteSound,
            "alert_sound": self.lineAlertSound,
            "alert_wait": self.spinWait,
            "termination_time": [t.time for t in self.times],
            "termination_enable": [t.checkbox for t in self.times],
        }

        self.lineIhFolder.setReadOnly(True)
        self.lineLisFolder.setReadOnly(True)
        self.lineCompleteSound.setReadOnly(True)
        self.lineAlertSound.setReadOnly(True)

        self.btnIhFolderSelector.clicked.connect(self.set_ih_folder)
        self.btnLisFolderSelector.clicked.connect(self.set_lis_folder)
        self.btnCompleteSoundSelector.clicked.connect(self.set_complete_sound)
        self.btnAlertSoundSelector.clicked.connect(self.set_alert_sound)

        self.pushTestCompleteSound.clicked.connect(self.test_complete_sound)
        self.pushTestAlertSound.clicked.connect(self.test_alert_sound)

        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.close)

        self.load()

    def load(self):
        settings = Settings("config.ini")

        for opt in settings.get_values().keys():
            item = self._settings[opt]
            if type(item) is QtWidgets.QLineEdit:
                item.setText(settings.get(opt))

            if type(item) is QtWidgets.QSpinBox:
                item.setValue(int(settings.get(opt)))

    def save(self):
        settings = Settings("config.ini")

        values = {}

        for opt in self._settings.keys():
            option = self._settings[opt]
            if type(option) is QtWidgets.QLineEdit:
                values[opt] = option.text()

            elif type(option) is QtWidgets.QSpinBox:
                values[opt] = str(option.value())

        settings.update(values)
        settings.save()
        self.close()

    def closeEvent(self, event):
        self.CLOSE.emit()
        super().closeEvent(event)

    def set_ih_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder != "":
            self.lineIhFolder.setText(folder)
        self.update()

    def set_lis_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder != "":
            self.lineLisFolder.setText(folder)
        self.update()

    def set_complete_sound(self):
        file = QFileDialog.getOpenFileName(self, "Select Sound File", "./", "mp3 file (*.mp3)")[0]
        if file != "":
            self.lineCompleteSound.setText(file)
        self.update()

    def set_alert_sound(self):
        file = QFileDialog.getOpenFileName(self, "Select Sound File", "./", "mp3 file (*.mp3)")[0]
        if file != "":
            self.lineAlertSound.setText(file)
        self.update()

    def test_complete_sound(self):
        alert.Alert("", audio_file=self.lineCompleteSound.text(), delay=0).start()

    def test_alert_sound(self):
        alert.Alert("", audio_file=self.lineAlertSound.text(), delay=0).start()


class TimeEdit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.time_edit = QtWidgets.QTimeEdit(self)
        self.time_edit.setDisplayFormat("hh:mm")

        self.enabled = QtWidgets.QCheckBox(self)
        self.enabled.setMaximumWidth(30)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.enabled)
        self.layout.addWidget(self.time_edit)
        self.enabled.clicked.connect(self.update)

        self.update()

    def update(self):
        if self.enabled.isChecked():
            self.time_edit.setDisabled(False)
        else:
            self.time_edit.setDisabled(True)
        super().update()

    @property
    def time(self):
        return self.time_edit

    @property
    def checkbox(self):
        return self.enabled


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)
    window = SettingWindow()
    window.show()
    sys.exit(app.exec())
