"""Create and verify the development environment without shell activation."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        print("Run this helper with Python 3.12 (for example: py -3.12 -m scripts.bootstrap).")
        return 1
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    env = os.environ.copy()
    env["PIP_CACHE_DIR"] = str(root / "data" / "cache" / "pip")
    env["PYTHONHASHSEED"] = "42"

    def run(*args: str) -> None:
        subprocess.run(args, cwd=root, env=env, check=True)

    try:
        if not python.exists():
            run(sys.executable, "-m", "venv", str(root / ".venv"))
        run(str(python), "-c", "import sys; sys.exit(0 if sys.version_info[:2] == (3,12) "
            "else 'Existing .venv is not Python 3.12; preserve it and select a separate environment')")
        run(str(python), "-m", "pip", "install", "--require-hashes", "-r", "requirements-dev.txt")
        run(str(python), "-m", "pip", "check")
        if not (root / ".env").exists():
            shutil.copyfile(root / ".env.example", root / ".env")
        run(str(python), "-m", "scripts.verify_corpus")
        run(str(python), "-m", "pytest", "-q")
    except subprocess.CalledProcessError as exc:
        print(f"Setup failed (exit code {exc.returncode}); see the command output above.")
        return exc.returncode
    print("Setup verified. Set PYTHONHASHSEED=42 in your shell before starting the server.")
    print("Start with the virtual environment's Python: -m scripts.serve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
