import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from playsound import playsound
from time import sleep


class Notify(threading.Thread):
    LOCK = threading.Lock()

    def __init__(self, sound, delay=0):
        super().__init__()
        self._sound = sound
        self._delay = delay

    def run(self):
        sleep(self._delay)
        self.LOCK.acquire()
        playsound(self._sound)
        print("提示音效播放中，請勿關閉視窗")
        print("若要取消，請按 CTRL+C")
        self.LOCK.release()


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
    def __init__(self):
        self._alert_sound = None
        self._alert_delay = 0

    def set_sound(self, sound_path):
        self._alert_sound = sound_path

    def set_delay(self, delay):
        self._alert_delay = delay

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

        if self._alert_sound is not None:
            Notify(self._alert_sound, self._alert_delay).start()

    def on_modified(self, event):
        if event.is_directory:
            print(f"{datetime.now()}: directory modified:{event.src_path}")
        else:
            print(f"{datetime.now()}: file modified:{event.src_path}")


if __name__ == "__main__":
    observer = ObserveCenter()
    event_handler = FileEventHandler()
    event_handler.set_sound("10-seconds-loop-2-97528.mp3")
    event_handler.set_delay(5)
    observer.schedule(event_handler, r"/home/lak/Documents/test", True)
    observer.start()
    try:
        while True:
            sleep(1)
            print(observer.get_run_time())

    except KeyboardInterrupt:
        observer.stop()

