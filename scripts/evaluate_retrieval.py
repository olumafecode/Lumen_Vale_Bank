"""Development retrieval check, separate from the held-out answer-quality benchmark."""
from datetime import datetime, timezone
import json
import time
from policy_assistant.config import PROJECT_ROOT
from policy_assistant.indexing import Retriever

if __name__ == "__main__":
    retriever = Retriever(PROJECT_ROOT)
    questions = [json.loads(line) for line in
                 (PROJECT_ROOT / "evaluation/development-questions.jsonl").read_text(encoding="utf-8-sig").splitlines()
                 if line.strip()]
    cases = []
    for item in questions:
        started = time.perf_counter()
        hits = retriever.search(item["question"], k=4)
        got = {h["metadata"]["section_id"] for h in hits}
        expected = set(item["expected_sections"])
        cases.append({"id": item["id"], "question": item["question"],
                      "expected_sections": sorted(expected), "retrieved_sections": sorted(got),
                      "any_expected_section_hit": bool(expected & got),
                      "expected_section_recall": len(expected & got) / len(expected),
                      "seconds": round(time.perf_counter() - started, 4), "hits": hits})
    report = {"scope": "five development prompts only; not final RAG evaluation",
              "created_at": datetime.now(timezone.utc).isoformat(),
              "fingerprint": retriever.record["fingerprint"], "k": 4,
              "any_hit_rate": sum(c["any_expected_section_hit"] for c in cases) / len(cases),
              "mean_expected_section_recall": sum(c["expected_section_recall"] for c in cases) / len(cases),
              "cases": cases}
    folder = PROJECT_ROOT / "evaluation/runs"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "development-retrieval.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
