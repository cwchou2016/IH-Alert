from configparser import ConfigParser
from os import path


class Settings:
    def __init__(self, f_name):
        self._f_name = f_name
        self._config = ConfigParser()
        self._config.add_section("setting")
        self._options = ["ih_folder", "lis_folder", "complete_sound", "alert_sound", "alert_wait"]
        self.reset()

    def reset(self):
        init_values = {
            "ih_folder": "",
            "lis_folder": "",
            "complete_sound": "audio/complete.mp3",
            "alert_sound": "audio/alert.mp3",
            "alert_wait": "60"
        }

        self.update(init_values)

    def load(self):
        if not path.isfile(self._f_name):
            return

        self._config.read(self._f_name)

    def update(self, value_dict):
        for opt in self._options:
            if value_dict.get(opt) is None:
                continue

            self._config.set("setting", opt, value_dict[opt])

    def save(self):
        with open(self._f_name, "w") as f:
            self._config.write(f)


if __name__ == "__main__":
    s = Settings("config.ini")
    # s.load()
    # s.update({"lis_folder": "sdf"})
    s.save()
    print((s._config))
