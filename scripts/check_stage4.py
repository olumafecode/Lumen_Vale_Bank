"""Development retrieval comparison only. Never reads held-out gold answers."""
import json
from datetime import datetime, timezone
from pathlib import Path

from policy_assistant.config import PROJECT_ROOT
from policy_assistant.retrieval import HybridRetriever
from policy_assistant.indexing import Retriever

def main():
    service = HybridRetriever(PROJECT_ROOT)
    questions = [json.loads(line) for line in
                 (PROJECT_ROOT / "evaluation/development-questions.jsonl").read_text().splitlines()]
    cases = []
    for case in questions:
        expected = set(case["expected_sections"])
        row = {"id": case["id"], "question": case["question"], "expected_sections": sorted(expected)}
        for method in ("dense", "hybrid"):
            hits = (Retriever.search(service, case["question"], k=4) if method == "dense"
                    else service.search(case["question"], k=4))
            found = {hit["metadata"]["section_id"] for hit in hits}
            row[method] = {"sections": sorted(found), "hit": bool(expected & found),
                           "recall": len(expected & found) / len(expected)}
        cases.append(row)
    result = {"scope": "five development prompts only; retrieval, not answer quality",
              "created_at": datetime.now(timezone.utc).isoformat(), "k": 4,
              "fingerprint": service.record["fingerprint"], "cases": cases}
    for method in ("dense", "hybrid"):
        result[method] = {"hit_rate": sum(c[method]["hit"] for c in cases) / len(cases),
                          "mean_section_recall": sum(c[method]["recall"] for c in cases) / len(cases)}
    destination = PROJECT_ROOT / "evaluation/runs/stage-4-retrieval.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
