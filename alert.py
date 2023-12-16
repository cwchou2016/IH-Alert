import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from playsound import playsound


class Notify(threading.Thread):
    def __init__(self, sound):
        super().__init__()
        self._sound = sound

    def run(self):
        playsound("10-seconds-loop-2-97528.mp3")
        print("提示音效播放中，請勿關閉視窗")
        print("若要取消，請按 CTRL+C")


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

        Notify("").start()

    def on_modified(self, event):
        if event.is_directory:
            print(f"{datetime.now()}: directory modified:{event.src_path}")
        else:
            print(f"{datetime.now()}: file modified:{event.src_path}")


if __name__ == "__main__":
    import time
    observer = Observer()
    event_handler = FileEventHandler()
    observer.schedule(event_handler, r"/home/lak/Documents/test", True)
    observer.start()
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        observer.stop()

