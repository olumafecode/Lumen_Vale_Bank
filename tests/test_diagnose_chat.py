import json

import pytest

from scripts.diagnose_chat import load_failed_cases


def test_failure_replay_uses_saved_evidence_and_excludes_gold(tmp_path):
    benchmark = [{"id": "Q1", "question": "Policy question?", "gold_answer": "DO NOT SEND"},
                 {"id": "Q2", "question": "Successful question?"}]
    hit = {"chunk_id": "saved-id", "text": "Saved policy passage", "metadata": {}}
    rows = [{"id": "Q1", "http_status": 502, "attempts": [{"retrieved": [hit]}]},
            {"id": "Q2", "http_status": 200, "attempts": []}]
    (tmp_path / "benchmark.json").write_text(json.dumps(benchmark), encoding="utf-8")
    source = "\n".join(json.dumps(row) for row in rows)
    (tmp_path / "responses.jsonl").write_text(source, encoding="utf-8")
    assert load_failed_cases(tmp_path) == [
        {"id": "Q1", "question": "Policy question?", "retrieved": [hit]}]
    assert (tmp_path / "responses.jsonl").read_text(encoding="utf-8") == source


def test_failure_replay_requires_saved_evidence(tmp_path):
    (tmp_path / "benchmark.json").write_text('[{"id":"Q1","question":"Question?"}]', encoding="utf-8")
    (tmp_path / "responses.jsonl").write_text(
        '{"id":"Q1","http_status":502,"attempts":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="no saved evidence"):
        load_failed_cases(tmp_path)
