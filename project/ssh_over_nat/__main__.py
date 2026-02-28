from pathlib import Path
import subprocess
import sys
import os

from .common import APP_NAME, get_app_cache_dir

project_root = Path(__file__).parent
dodo_path = project_root / "dodo.py"


def main():
    if not dodo_path.exists():
        raise RuntimeError(f"dodo.py not found at {project_root}")

    cache_dir = get_app_cache_dir(APP_NAME)
    os.environ["PYTHONPYCACHEPREFIX"] = str(cache_dir / "pycache")
    args = sys.argv[1:] if len(sys.argv) > 1 else ["help"]

    cmd = [
        sys.executable,
        "-m",
        "doit",
        "-f",
        dodo_path,
        *args,
    ]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
