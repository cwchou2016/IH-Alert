import threading

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


class FileEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        pass

    def on_moved(self, event):
        if event.is_directory:
            print(f"{datetime.now()}: directory moved from {event.src_path} to {event.dest_path}")
        else:
            print(f"{datetime.now()}: file moved from {event.src_path} to {event.dest_path}")

    def on_created(self, event):
        if event.is_directory:
            print(f"{datetime.now()}: directory created:{event.src_path}")
        else:
            print(f"{datetime.now()}: file created:{event.src_path}")

    def on_deleted(self, event):
        if event.is_directory:
            print(f"{datetime.now()}: directory deleted:{event.src_path}")
        else:
            print(f"{datetime.now()}: file deleted:{event.src_path}")

    def on_modified(self, event):
        if event.is_directory:
            print(f"{datetime.now()}: directory modified:{event.src_path}")
        else:
            print(f"{datetime.now()}: file modified:{event.src_path}")


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
    import os


    class LisFolderHandler(FileEventHandler):
        def on_deleted(self, event):
            if event.is_directory:
                return
            print("lis")
            Notification("", audio_file="10-seconds-loop-2-97528.mp3").start()


    class IhFolderHandler(FileEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return

            dir_folder, f_name = os.path.split(event.src_path)

            if os.path.basename(dir_folder) != "Results":
                return

            _, ext = os.path.splitext(f_name)
            if ext.lower() == ".xml":
                sample = SampleTest.read_xml(event.src_path)
                print(datetime.now(), sample.sample_id, sample.assays, os.path.getsize(event.src_path))

            if ext.lower() == ".upl":
                sample = SampleTest.read_upl(event.src_path)
                print(datetime.now(), sample.sample_id, sample.assays)


    observer = ObserveCenter()
    event_handler = IhFolderHandler()
    observer.schedule(event_handler, r"/home/lak/Documents/test", True)
    observer.start()
    try:
        while True:
            sleep(1)
            # print(observer.get_run_time())

    except KeyboardInterrupt:
        observer.stop()
