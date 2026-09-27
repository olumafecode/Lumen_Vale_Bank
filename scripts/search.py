"""Inspect retrieved evidence from the real local vector index."""
import argparse
import json
from policy_assistant.config import PROJECT_ROOT
from policy_assistant.indexing import Retriever

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(Retriever(PROJECT_ROOT).search(args.question, args.k), indent=2, ensure_ascii=False))
