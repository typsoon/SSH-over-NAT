from pathlib import Path
import subprocess
import sys
import os

from .common import APP_NAME, get_app_cache_dir

project_root = Path(__file__).parents[0]
dodo_path = project_root / "dodo.py"


def main():
    if not dodo_path.exists():
        raise RuntimeError(f"dodo.py not found at {project_root}")

    cache_dir = get_app_cache_dir(APP_NAME)

    os.environ["PYTHONPYCACHEPREFIX"] = os.path.join(cache_dir, "pycache")

    cmd = [sys.executable, "-m", "doit", "-f", dodo_path, *sys.argv[1:]]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
