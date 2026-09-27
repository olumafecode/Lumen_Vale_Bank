"""Resolve hashed locks, install Stage 3 packages, and download the pinned model."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info[:2] != (3, 12) or sys.prefix == sys.base_prefix:
        raise SystemExit("Use the project's Python 3.12 virtual environment.")
    env = os.environ.copy()
    env["PIP_CACHE_DIR"] = str(ROOT / "data/cache/pip")
    env["PYTHONHASHSEED"] = "42"
    common = ["--cache-dir", "data/cache/pip-tools", "--generate-hashes",
              "--allow-unsafe", "--strip-extras", "--no-emit-index-url",
              "--no-emit-trusted-host", "--quiet"]
    for name in ("requirements", "requirements-dev"):
        print(f"Resolving hashed {name}.txt...", flush=True)
        command = [sys.executable, "-m", "piptools", "compile", *common,
                   "--output-file", name + ".txt", name + ".in"]
        env["CUSTOM_COMPILE_COMMAND"] = "python -m piptools compile " + " ".join(command[4:])
        subprocess.run(command, cwd=ROOT, env=env, check=True)
    print("Installing the resolved packages...", flush=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--require-hashes",
                    "-r", "requirements-dev.txt"], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, "-m", "pip", "check"], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, "-m", "scripts.prepare_model"],
                   cwd=ROOT, env=env, check=True)
    print("Stage 3 dependencies and model are ready. No index has been built by this command.")


if __name__ == "__main__":
    main()
