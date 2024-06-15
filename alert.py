import shutil
import subprocess
import threading
import os

from PySide6.QtCore import QObject, Signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from playsound import playsound
from gtts import gTTS
from time import sleep
import xmltodict


def send_result_to_lis():
    try:
        _org_dir = os.getcwd()
        os.chdir(r"c:\automation")
        subprocess.run([r"AutomationNet.exe"])
        os.chdir(_org_dir)
    except Exception as e:
        print(e)


class Notification(threading.Thread):
    LOCK = threading.Lock()

    def __init__(self, name, *, audio_file=None, delay=0, out_folder="audio/out/"):
        super().__init__()
        self._delay = delay
        self._name = name
        self._event = threading.Event()
        self._second = 0
        self._sound = audio_file
        self._out = out_folder

        if not os.path.isdir(self._out):
            os.mkdir(self._out)

    def run(self):

        while True:
            if self._event.is_set():
                self.on_stop()
                break

            self._event.wait(1)
            if self._second == self._delay:
                self.on_notify()
                break

            self._second += 1

        self.on_complete()

    def playsound(self):
        if self._sound is None:
            return

        playsound(self._sound)

    def say_last_3_char(self):
        last_3 = self._name[-3:]
        audio_file = f"{self._out}{last_3}.mp3"

        if not os.path.isfile(audio_file):
            to_speak = " ".join([c for c in last_3])
            tts = gTTS(f" {to_speak} 。已完成", lang="zh-tw", slow=True)
            tts.save(audio_file)

        playsound(audio_file)

    def stop(self):
        self._event.set()

    def on_stop(self):
        print("Interrupted")

    def on_notify(self):
        is_locked = self.LOCK.locked()

        self.LOCK.acquire()
        send_result_to_lis()

        if not is_locked:
            self.playsound()

        self.say_last_3_char()
        self.LOCK.release()

    def on_complete(self):
        print(f"{self._name} is Completed")

    @property
    def name(self):
        return self._name


class Alert(Notification):
    def on_notify(self):
        self.playsound()


class ObserveCenter(Observer):
    def __init__(self):
        super().__init__()
        self._start_time = None

    def start(self):
        self._start_time = datetime.now()
        super().start()

    def stop(self):
        self._start_time = None
        super().stop()

    def get_run_time(self):
        if self._start_time is None:
            return -1

        return (datetime.now() - self._start_time).seconds


class SampleTest:
    """
    Store information of samples,
    including sample numbers and assays used in the tests
    """

    def __init__(self, sample_number: str, assays: list[str]):
        self._id = sample_number
        self._assays = assays

    @classmethod
    def read_xml(cls, file):
        res = XmlResult.read_file(file)
        return SampleTest(res.sample_id, res.assays)

    @classmethod
    def read_upl(cls, file):
        sample_id, assays = None, []
        with open(file, "r") as f:
            for line in f.readlines():
                l = line.split("|")
                if l[0] == "P":
                    sample_id = l[3]

                if l[0] == "O":
                    assays.append(l[4].strip("^"))

        return SampleTest(sample_id, assays)

    @property
    def sample_id(self):
        return self._id

    @property
    def assays(self):
        return self._assays


class LisFolderHandler(FileSystemEventHandler, QObject):
    DELETED = Signal(SampleTest)

    def __init__(self, *, audio_file=None, delay=0):
        QObject.__init__(self)
        self._audio = audio_file
        self._delay = delay
        self._last_modified = None

    def on_modified(self, event):
        if self._last_modified == event.src_path:
            return
        if event.is_directory:
            return

        self._last_modified = event.src_path

        print(f"{datetime.now()}: Modified {event.src_path}")
        _, f_name = os.path.split(event.src_path)
        _, ext = os.path.splitext(f_name)

        if ext.lower() == ".upl":
            sample = SampleTest("Unknown", [])
            try:
                sample = SampleTest.read_upl(event.src_path)
            except Exception as e:
                print(e)
            self.DELETED.emit(sample)
            Notification(sample.sample_id, audio_file=self._audio, delay=self._delay).start()


class IhFolderHandler(FileSystemEventHandler, QObject):
    RECEIVED = Signal(SampleTest)
    CONFIRMED = Signal(SampleTest)

    def __init__(self, *, audio_file=None, delay=10):
        QObject.__init__(self)
        self._notifications = {}
        self._audio = audio_file
        self._delay = delay
        self._last_modified = None

    def on_modified(self, event):
        if self._last_modified == event.src_path:
            return
        if event.is_directory:
            return

        self._last_modified = event.src_path

        print(f"{datetime.now()}: Modified {event.src_path}")

        if not self.is_target_files(event.src_path):
            return

        sample = SampleTest("unknown", [])
        _, ext = os.path.splitext(event.src_path)
        if ext.lower() == ".xml":
            try:
                sample = SampleTest.read_xml(event.src_path)
            except Exception as e:
                print(e)
            print(datetime.now(), sample.sample_id, sample.assays)

            if sample.sample_id in self.notifications:
                print(f"{sample.sample_id} has been registered!")
                return

            self.RECEIVED.emit(sample)

            if "PR15B" in sample.assays:
                notification = Alert(sample.sample_id, audio_file=self._audio, delay=self._delay)
                notification.start()
                self.add_notification(sample.sample_id, notification)

        elif ext.lower() == ".upl":
            try:
                sample = SampleTest.read_upl(event.src_path)
            except Exception as e:
                print(e)
            print(datetime.now(), sample.sample_id, sample.assays)

            self.CONFIRMED.emit(sample)

            if sample.sample_id not in self.notifications:
                print(f"{sample.sample_id} is not registered!")
                return

            if "PR15B" in sample.assays:
                self.remove_notification(sample.sample_id)

    def is_target_files(self, file):
        dir_folder, f_name = os.path.split(file)
        parent_folder = os.path.dirname(dir_folder)

        if os.path.basename(dir_folder) != "Backup":
            return False

        if os.path.basename(parent_folder) != "Results":
            return False

        return True

    @property
    def notifications(self):
        self.refresh_notifications()
        return self._notifications.keys()

    def add_notification(self, sample_id: str, notification: Notification):
        self._notifications[sample_id] = notification

    def remove_notification(self, sample_id: str):
        self._notifications[sample_id].stop()
        del (self._notifications[sample_id])

    def refresh_notifications(self):
        to_remove = []

        for sample in self._notifications:
            if not self._notifications[sample].is_alive():
                to_remove.append(sample)

        for sample in to_remove:
            self.remove_notification(sample)


class XmlResult:
    """
    Read results from xml file
    """

    def __init__(self, data=None):
        self.data = data

    @classmethod
    def read_file(cls, f_name):
        with open(f_name, "r") as f:
            data = xmltodict.parse(f.read())

        return XmlResult(data)

    @property
    def sample_id(self):
        return self.data['RESULT']['RESULT']['SampleBarcode']

    @property
    def assays(self):
        return [self.data['RESULT']['RESULT']['AssayCode']]


if __name__ == "__main__":
    from settings import Settings

    settings = Settings("config.ini")

    observer = ObserveCenter()
    ih_handler = IhFolderHandler(audio_file=settings.get("alert_sound"), delay=int(10))
    lis_handler = LisFolderHandler(audio_file=settings.get("complete_sound"))
    observer.schedule(ih_handler, settings.get("ih_folder"), True)
    observer.schedule(lis_handler, settings.get("lis_folder"), False)
    observer.start()
    try:
        while True:
            sleep(1)
            # print(observer.get_run_time())

    except KeyboardInterrupt:
        observer.stop()
