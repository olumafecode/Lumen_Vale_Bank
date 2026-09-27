"""Explicit, free one-time model download; no API credentials are used."""
import json
from policy_assistant.config import PROJECT_ROOT
from policy_assistant.embedding import prepare_model

if __name__ == "__main__":
    print("Downloading/verifying the pinned MiniLM model; the first run may take a few minutes.", flush=True)
    record = prepare_model(PROJECT_ROOT)
    print(json.dumps({"status": "ready", "model": record["model"],
                      "dimensions": record["dimensions"],
                      "archive_sha256": record["archive_sha256"]}, indent=2))
