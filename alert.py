import threading
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from playsound import playsound
from time import sleep
import xmltodict


class Notification(threading.Thread):
    LOCK = threading.Lock()

    def __init__(self, name, *, audio_file=None, delay=0):
        super().__init__()
        self._delay = delay
        self._name = name
        self._event = threading.Event()
        self._second = 0
        self._sound = audio_file

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
        playsound(self._sound)

    def stop(self):
        self._event.set()

    def on_stop(self):
        print("Interrupted")

    def on_notify(self):
        print("Notify")

    def on_complete(self):
        print("Completed")

    @property
    def name(self):
        return self._name


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


class LisFolderHandler(FileSystemEventHandler):
    def __init__(self, audio_file=None):
        self._audio = audio_file

    def on_deleted(self, event):
        if event.is_directory:
            return
        Notification("", audio_file="10-seconds-loop-2-97528.mp3").start()


class IhFolderHandler(FileSystemEventHandler):
    def __init__(self, audio_file=None):
        self._samples = {}
        self._audio = audio_file

    def on_modified(self, event):
        if event.is_directory:
            return

    @property
    def samples(self):
        return self._samples.keys()

    def add_sample(self, sample_id: str, notification: Notification):
        self._samples[sample_id] = notification

    def remove_sample(self, sample_id: str):
        self._samples[sample_id].stop()
        del (self._samples[sample_id])


class XmlResult:
    """
    Read results from xml file
    """

    def __init__(self, data=None):
        self.data = data

    @classmethod
    def read_file(cls, f_name):
        data = None
        with open(f_name, "r") as f:
            data = xmltodict.parse(f.read())

        return XmlResult(data)

    @property
    def sample_id(self):
        return self.data['RESULT']['RESULT']['SampleBarcode']

    @property
    def assays(self):
        return [self.data['RESULT']['RESULT']['AssayCode']]


class SampleTest:
    """
    Store information of samples,
    including sample numbers and assays used in the tests
    """

    def __init__(self, sample_number: int, assays: list[str]):
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


if __name__ == "__main__":

    observer = ObserveCenter()
    # ih_handler = IhFolderHandler()
    lis_handler = LisFolderHandler()
    # observer.schedule(ih_handler, r"/home/lak/Documents/test/Results", False)
    observer.schedule(lis_handler, r"/home/lak/Documents/test", False)
    observer.start()
    try:
        while True:
            sleep(1)
            # print(observer.get_run_time())

    except KeyboardInterrupt:
        observer.stop()
