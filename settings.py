from configparser import ConfigParser
from os import path


class Settings:
    def __init__(self, f_name):
        self._f_name = f_name
        self._config = ConfigParser()

    def load(self):
        if not path.isfile(self._f_name):
            return

        self._config.read(self._f_name)

    def save(self):
        with open(self._f_name, "w") as f:
            self._config.write(f)


if __name__ == "__main__":
    s = Settings("config.ini")
    s.load()
    s.save()
    print((s._config))
