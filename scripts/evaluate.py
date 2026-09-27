"""Frozen held-out evaluation through a private loopback HTTP server."""
import argparse
import copy
from datetime import datetime, timezone
import importlib.metadata
import json
import platform
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid

from waitress import create_server
from policy_assistant import create_app
from policy_assistant.config import PROJECT_ROOT, Settings
from policy_assistant.generation import ProviderSettings, SYSTEM_PROMPT
from policy_assistant.chat import PROMPT_VERSION
from policy_assistant.retrieval import HybridRetriever
from .evaluation_support import digest, write_json, measurements, review_files


def snapshot(root):
    paths = [root / "app.py", root / "requirements.txt", root / "requirements-dev.txt",
             root / "corpus-manifest.json", root / "evaluation/questions.jsonl"]
    for name in ("policy_assistant", "scripts"):
        paths += sorted((root / name).rglob("*.py"))
    return {p.relative_to(root).as_posix(): digest(p) for p in paths}


def call(url, question):
    req = urllib.request.Request(url, data=json.dumps({"question": question}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read())
        except ValueError:
            body = {"error": "Non-JSON HTTP error"}
        return exc.code, body
    except (OSError, ValueError):
        return 0, {"error": "Client transport or response-decoding failure"}


def request_case(url, case, captured, retry_wait, max_retries):
    attempts = []
    start = time.perf_counter()
    for number in range(max_retries + 1):
        captured.clear()
        attempt_start = time.perf_counter()
        status, body = call(url, case["question"])
        attempts.append({"http_status": status, "response": body,
                         "duration_seconds": time.perf_counter() - attempt_start,
                         "retrieved": copy.deepcopy(captured)})
        if status != 429 or number == max_retries:
            break
        print(f"{case['id']}: HTTP 429; waiting {retry_wait:g}s before one retry.", flush=True)
        time.sleep(retry_wait)
    return {"id": case["id"], "http_status": status, "response": body,
            "duration_seconds": time.perf_counter() - start, "attempts": attempts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=30, help="Seconds between cases; outside request timer.")
    parser.add_argument("--retry-wait", type=float, default=65, help="429 retry wait; included in request timer.")
    args = parser.parse_args()
    if not 0 <= args.delay <= 300 or not 1 <= args.retry_wait <= 300:
        parser.error("delay must be 0–300 and retry-wait 1–300 seconds")
    root = PROJECT_ROOT
    settings = Settings.from_environment()
    provider = ProviderSettings.from_environment()
    if not provider.configured:
        raise SystemExit("Configure GROQ_API_KEY in .env before evaluation.")
    frozen = snapshot(root)
    cases = [json.loads(line) for line in (root / "evaluation/questions.jsonl").read_text().splitlines()]
    if [q["id"] for q in cases] != [f"Q{i:02}" for i in range(1, 26)]:
        raise SystemExit("Expected the original ordered Q01–Q25 benchmark.")
    captured = []
    class CapturingRetriever(HybridRetriever):
        def search(self, question, k=4):
            hits = super().search(question, k)
            captured[:] = copy.deepcopy(hits)
            return hits
    startup = time.perf_counter()
    app = create_app(settings, retriever_factory=CapturingRetriever)
    health = app.test_client().get("/health").get_json()
    if not health.get("rag_ready"):
        raise SystemExit("Local retrieval is not ready. Check corpus, model cache, and index.")
    server = create_server(app, host="127.0.0.1", port=0, threads=2)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    directory = root / "evaluation/runs" / run_id
    directory.mkdir(parents=True)
    try:
        revision = subprocess.run(["git", "-c", "safe.directory=" + str(root),
                                   "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
        revision = revision.stdout.strip() if revision.returncode == 0 else "uncommitted"
    except OSError:
        revision = "unavailable"
    metadata = {"run_id": run_id, "status": "running", "created_at": datetime.now(timezone.utc).isoformat(),
                "code_revision": revision, "file_hashes": frozen, "benchmark_sha256": digest(root / "evaluation/questions.jsonl"),
                "provider": "groq", "model": provider.model, "temperature": 0,
                "max_completion_tokens": 2048, "reasoning_effort": "low" if provider.model.startswith("openai/gpt-oss-") else "provider_default",
                "prompt_version": PROMPT_VERSION, "system_prompt": SYSTEM_PROMPT,
                "response_format": "strict_json_schema_with_retrieved_chunk_id_enum",
                "retrieval": {"method": "BM25+dense RRF", "k_per_question": 4, "max_context_chunks": 12, "max_question_parts": 3, "candidates_each": 20, "rrf_constant": 60},
                "index": json.loads((root / "data/index/active.json").read_text()),
                "python": platform.python_version(), "os": platform.platform(),
                "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
                "pacing_seconds": args.delay, "max_429_retries": 1, "retry_wait_seconds": args.retry_wait,
                "provider_format_retries": 1, "provider_timeout_budget_seconds": 30,
                "answer_cache": False, "startup_seconds": time.perf_counter() - startup,
                "seeds": {"random": settings.random_seed},
                "benchmark_exposure": "First run is held-out. Subsequent code changes informed by these results invalidate an unbiased held-out claim."}
    (directory / "benchmark.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    write_json(directory / "run.json", metadata)
    results = []
    print("Run directory: " + str(directory), flush=True)
    url = "http://127.0.0.1:" + str(server.effective_port) + "/chat"
    try:
        warm = request_case(url, {"id": "warmup", "question": "How many annual leave days do full-time staff receive?"},
                            captured, args.retry_wait, 1)
        write_json(directory / "warmup.json", warm)
        if warm["http_status"] != 200:
            raise RuntimeError("Warm-up failed; no scored cases sent. Check warmup.json.")
        for case in cases:
            time.sleep(args.delay)
            if snapshot(root) != frozen:
                raise RuntimeError("Code, corpus manifest, dependencies, or benchmark changed during the run.")
            row = request_case(url, case, captured, args.retry_wait, 1)
            results.append(row)
            with (directory / "responses.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
            write_json(directory / "metrics.json", measurements(cases, results))
            print(f"{case['id']}: HTTP {row['http_status']}, {row['duration_seconds']:.3f}s, "
                  f"refused={row['response'].get('refused', 'n/a')}", flush=True)
            if row["http_status"] in (0, 503, 504):
                raise RuntimeError("Connectivity or readiness failed; saved partial run. Do not overwrite it.")
        if snapshot(root) != frozen:
            raise RuntimeError("Files changed during the last request; run invalid.")
        metadata["status"] = "complete"
    except (Exception, KeyboardInterrupt) as exc:
        metadata["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "incomplete"
        metadata["stop_reason"] = str(exc) or "Interrupted by user"
        print(metadata["stop_reason"], flush=True)
    finally:
        metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
        metadata["cases_recorded"] = len(results)
        write_json(directory / "run.json", metadata)
        write_json(directory / "metrics.json", measurements(cases, results))
        review_files(directory, cases, results)
        server.close()
    print("Saved raw evidence, metrics, review.csv, and review-packet.md.", flush=True)
    print("No groundedness or citation-accuracy score is claimed until human review.", flush=True)
    if metadata["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
