import csv
import json
from types import SimpleNamespace

import pytest

from scripts import evaluate
from scripts.evaluation_support import measurements, nearest_rank, quality, REVIEW_FIELDS, review_files

CASES = [{"id": "Q01", "type": "answerable", "topic": "test", "question": "question",
          "gold_answer": "gold", "required_points": ["point"]},
         {"id": "Q02", "type": "answerable", "topic": "test", "question": "question2",
          "gold_answer": "gold2", "required_points": ["point"]},
         {"id": "Q03", "type": "guardrail", "topic": "test", "question": "outside",
          "gold_answer": "refuse", "required_points": ["refuse"]}]


def row(id, status=200, refused=False, seconds=1):
    return {"id": id, "http_status": status, "duration_seconds": seconds,
            "response": {"answer": "text", "refused": refused}, "attempts": [{"retrieved": []}]}


def test_nearest_rank_and_failure_denominators():
    assert nearest_rank(list(range(1, 21)), .5) == 10
    assert nearest_rank(list(range(1, 21)), .95) == 19
    assert nearest_rank([], .95) is None
    result = measurements(CASES, [row("Q01", seconds=3), row("Q02", status=429, seconds=65)])
    assert result["coverage"] == .5
    assert result["latency_sample_size"] == 1
    assert result["p95_seconds_nearest_rank"] == 3
    assert result["failed_requests"][0]["seconds"] == 65
    assert result["http_failure_rate_among_attempted"] == .5


def test_refusal_is_http_completion_but_not_coverage():
    result = measurements(CASES, [row("Q01", refused=True)])
    assert result["http_completed"] == 1
    assert result["substantive_answers"] == 0
    assert result["answerable_total"] == 2


def test_review_requires_human_and_preserves_work(tmp_path):
    review_files(tmp_path, CASES, [])
    path = tmp_path / "review.csv"
    original = path.read_bytes()
    review_files(tmp_path, CASES, [row("Q01")])
    assert path.read_bytes() == original
    assert quality(CASES, [], path)["status"] == "human_review_pending"


def write_review(path, reviewer_type="human", invalid_credit=False, notes="Checked against captured evidence"):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for q in CASES:
            fields = {"id": q["id"], "reviewer": "Reviewer", "reviewer_type": reviewer_type,
                      "notes": notes}
            if q["type"] == "answerable":
                value = "1" if q["id"] == "Q01" or invalid_credit else "0"
                fields.update(grounded=value, citation_accurate=value, required_points_met=value)
            else:
                fields["guardrail_correct"] = "1"
            writer.writerow(fields)


def test_strict_and_answer_only_denominators(tmp_path):
    path = tmp_path / "review.csv"
    write_review(path)
    scores = quality(CASES, [row("Q01"), row("Q02", status=502), row("Q03", refused=True)], path)
    assert scores["groundedness_strict"] == .5
    assert scores["citation_accuracy_answer_only"] == 1
    assert scores["answer_only_denominator"] == 1
    assert scores["guardrail_passes"] == 1


def test_notes_are_optional_but_human_review_is_required(tmp_path):
    path = tmp_path / "review.csv"
    results = [row("Q01"), row("Q02", status=502), row("Q03", refused=True)]
    write_review(path, notes="")
    assert quality(CASES, results, path)["status"] == "human_reviewed"
    write_review(path, reviewer_type="ai", notes="")
    assert quality(CASES, results, path)["status"] == "human_review_pending"


def test_ai_only_review_and_false_failure_credit_rejected(tmp_path):
    path = tmp_path / "review.csv"
    results = [row("Q01"), row("Q02", status=502), row("Q03", refused=True)]
    write_review(path, "ai")
    assert quality(CASES, results, path)["status"] == "human_review_pending"
    write_review(path, invalid_credit=True)
    with pytest.raises(ValueError, match="no substantive answer"):
        quality(CASES, results, path)


def test_retry_is_preserved_and_wait_included(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(evaluate.time, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(evaluate.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    responses = iter([(429, {"error": "limit"}), (200, {"answer": "answer", "refused": False})])
    captured = []
    def fake_call(url, question):
        clock[0] += 1
        captured.append({"text": "retrieved evidence"})
        return next(responses)
    monkeypatch.setattr(evaluate, "call", fake_call)
    result = evaluate.request_case("http://localhost/chat", {"id": "Q01", "question": "q"}, captured, 65, 1)
    assert result["duration_seconds"] == 67
    assert [a["http_status"] for a in result["attempts"]] == [429, 200]
    assert all(len(a["retrieved"]) == 1 for a in result["attempts"])


def test_only_question_is_sent_not_gold(monkeypatch):
    import io
    class Response(io.BytesIO):
        status = 200
    def urlopen(request, timeout):
        assert json.loads(request.data) == {"question": "policy question"}
        assert timeout == 45
        return Response(b'{"answer":"result"}')
    monkeypatch.setattr(evaluate.urllib.request, "urlopen", urlopen)
    assert evaluate.call("http://127.0.0.1:1234/chat", "policy question") == (200, {"answer": "result"})


def test_complete_runner_saves_all_cases_without_provider_calls(monkeypatch, tmp_path):
    from pathlib import Path
    root = tmp_path
    (root / "evaluation").mkdir()
    (root / "data/index").mkdir(parents=True)
    for name in ("app.py", "requirements.txt", "requirements-dev.txt", "corpus-manifest.json"):
        (root / name).write_text("test snapshot")
    (root / "data/index/active.json").write_text('{"fingerprint":"test"}')
    cases = [dict(CASES[0], id=f"Q{i:02}", type="answerable" if i <= 20 else "guardrail")
             for i in range(1, 26)]
    (root / "evaluation/questions.jsonl").write_text("\n".join(json.dumps(q) for q in cases))
    class Server:
        effective_port = 12345
        def run(self): pass
        def close(self): pass
    health_client = SimpleNamespace(get=lambda _: SimpleNamespace(get_json=lambda: {"rag_ready": True}))
    monkeypatch.setattr(evaluate, "PROJECT_ROOT", root)
    monkeypatch.setattr(evaluate.Settings, "from_environment", lambda: SimpleNamespace(random_seed=42))
    monkeypatch.setattr(evaluate.ProviderSettings, "from_environment",
                        lambda: SimpleNamespace(configured=True, model="test"))
    monkeypatch.setattr(evaluate, "create_app", lambda *a, **k: SimpleNamespace(test_client=lambda: health_client))
    monkeypatch.setattr(evaluate, "create_server", lambda *a, **k: Server())
    monkeypatch.setattr(evaluate.time, "sleep", lambda _: None)
    calls = []
    def response(url, question):
        calls.append(question)
        return 200, {"answer": "test response", "refused": False}
    monkeypatch.setattr(evaluate, "call", response)
    monkeypatch.setattr("sys.argv", ["evaluate", "--delay", "0"])
    evaluate.main()
    folders = list((root / "evaluation/runs").iterdir())
    assert len(folders) == 1 and len(calls) == 26
    folder = folders[0]
    record = json.loads((folder / "run.json").read_text())
    assert record["status"] == "complete"
    assert record["cases_recorded"] == 25
    assert len((folder / "responses.jsonl").read_text().splitlines()) == 25
    stats = json.loads((folder / "metrics.json").read_text())
    assert stats["latency_sample_size"] == 20
    assert (folder / "warmup.json").exists()
    assert (folder / "review.csv").exists()
