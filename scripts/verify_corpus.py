"""Validate canonical source files. This does not build a vector index."""

import json

from policy_assistant.config import PROJECT_ROOT
from policy_assistant.corpus import CorpusError, verify_corpus


def main() -> int:
    try:
        print(json.dumps(verify_corpus(PROJECT_ROOT), indent=2))
        return 0
    except CorpusError as exc:
        print(f"Corpus verification failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
