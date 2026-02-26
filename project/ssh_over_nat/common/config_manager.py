from platformdirs import user_config_dir
from pathlib import Path
import json
from enum import Enum

CONFIG_FILE = "environment.json"


class GlobalConfig:
    def __init__(self, enum_class: type[Enum], app_name, set_at_start=None):
        self.enum_class = enum_class
        config_dir = Path(user_config_dir(app_name))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.path = config_dir / CONFIG_FILE
        if not self.path.exists():
            self._write({})

        if set_at_start is not None:
            for key, val in set_at_start.items():
                if self.get(key, None) is None:
                    self.set(key, val)

    def _read(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _check_key(self, key):
        if isinstance(key, Enum):
            key_name = key.name
        elif isinstance(key, str):
            key_name = key
            if key_name not in [e.name for e in self.enum_class]:
                raise KeyError(f"Invalid key: {key_name}")
        else:
            raise TypeError("Key must be an Enum or string")
        return key_name

    def get(self, key, default=None):
        key_name = self._check_key(key)
        return self._read().get(key_name, default)

    def set(self, key, value):
        key_name = self._check_key(key)
        data = self._read()
        data[key_name] = value
        self._write(data)

    def all(self) -> dict:
        return self._read()
