from pathlib import Path
from platformdirs import user_cache_dir
import os


def get_app_cache_dir(app_name) -> Path:
    cache_dir = user_cache_dir(app_name)
    os.makedirs(cache_dir, exist_ok=True)
    return Path(cache_dir)
