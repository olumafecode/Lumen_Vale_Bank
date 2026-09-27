"""Build local embeddings and a persistent vector index; never call an LLM."""
import argparse
import json
from policy_assistant.config import PROJECT_ROOT
from policy_assistant.indexing import build_index

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--overlap", type=int, default=30)
    args = parser.parse_args()
    print(json.dumps(build_index(PROJECT_ROOT, args.max_tokens, args.overlap), indent=2))
