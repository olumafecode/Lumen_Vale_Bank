"""Small validated configuration; machine-specific paths never enter the repository."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _integer(name: str, default: int, low: int, high: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} must be an integer") from None
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return value


@dataclass(frozen=True)
class Settings:
    project_root: Path
    host: str
    port: int
    random_seed: int

    @classmethod
    def from_environment(cls, root: Path = PROJECT_ROOT) -> "Settings":
        root = root.resolve()
        # The process environment takes precedence; read only this project's .env.
        load_dotenv(root / ".env", override=False)
        host = os.environ.get("APP_HOST", "127.0.0.1").strip()
        if not host or any(c.isspace() for c in host) or "://" in host:
            raise ValueError("APP_HOST must be a hostname or IP address")
        return cls(root, host, _integer("APP_PORT", 8000, 1, 65535),
                   _integer("RANDOM_SEED", 42, 0, 2**32 - 1))
