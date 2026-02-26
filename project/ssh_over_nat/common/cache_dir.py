from platformdirs import user_cache_dir
import os


def get_app_cache_dir(app_name):
    cache_dir = user_cache_dir(app_name)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir
