"""Diagnose development prompts or explicitly labeled benchmark-failure replays."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import io
import time
import urllib.error
import urllib.request
import uuid
from unittest.mock import patch

from policy_assistant.config import PROJECT_ROOT, Settings
from policy_assistant.generation import GroqGenerator, ProviderSettings, ProviderError
from policy_assistant.retrieval import HybridRetriever
from policy_assistant.chat import validate_answer, AnswerValidationError, PROMPT_VERSION



def load_failed_cases(directory):
    """Select failed questions and frozen evidence, never gold answers."""
    directory = Path(directory)
    benchmark = json.loads((directory / "benchmark.json").read_text(encoding="utf-8"))
    questions = {item["id"]: item["question"] for item in benchmark}
    responses = [json.loads(line) for line in
                 (directory / "responses.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    cases = []
    for row in responses:
        if row["http_status"] == 200:
            continue
        attempts = row.get("attempts", [])
        hits = attempts[-1].get("retrieved", []) if attempts else []
        if not hits:
            raise ValueError("Failed case has no saved evidence: " + row["id"])
        cases.append({"id": row["id"], "question": questions[row["id"]], "retrieved": hits})
    if not cases:
        raise ValueError("Run has no failed requests to diagnose")
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=30)
    parser.add_argument("--failed-run", type=Path, help="Replay failures from a saved run; this is benchmark-informed diagnosis, not a scored evaluation.")
    args = parser.parse_args()
    if not 0 <= args.delay <= 300:
        parser.error("delay must be between 0 and 300")
    Settings.from_environment()
    provider = ProviderSettings.from_environment()
    if not provider.configured:
        raise SystemExit("Configure GROQ_API_KEY in .env first.")
    development = {q["id"]: q for q in [
        json.loads(line) for line in (PROJECT_ROOT / "evaluation/development-questions.jsonl").read_text().splitlines()]}
    cases = [
        {"id": "D01-control", "question": development["D01"]["question"]},
        {"id": "D01+D05", "question": development["D01"]["question"] + " Also, " + development["D05"]["question"]},
        {"id": "D02+D03", "question": development["D02"]["question"] + " Also, " + development["D03"]["question"]}
    ]
    if args.failed_run:
        try:
            cases = load_failed_cases(args.failed_run)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(str(exc))
    retriever = None if args.failed_run else HybridRetriever(PROJECT_ROOT)
    generator = GroqGenerator(provider)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    path = PROJECT_ROOT / "evaluation/runs" / ("diagnostic-" + run_id + ".json")
    report = {"scope": ("benchmark-informed failure replay; not a new held-out evaluation or replacement result"
                        if args.failed_run else "development formatting diagnosis; not held-out evaluation"),
              "source_run": args.failed_run.name if args.failed_run else None,
              "model": provider.model, "prompt_version": PROMPT_VERSION,
              "index_fingerprint": retriever.record["fingerprint"] if retriever else None,
              "evidence_mode": "saved retrieval" if args.failed_run else "current retrieval", "results": []}
    actual_urlopen = urllib.request.urlopen
    provider_failure = {}
    def observed_urlopen(*a, **kw):
        try:
            return actual_urlopen(*a, **kw)
        except urllib.error.HTTPError as exc:
            provider_failure["http_status"] = exc.code
            # Save only selected diagnostic fields. Never record authorization headers,
            # .env content, raw request objects, or unrestricted error messages.
            try:
                error_bytes = exc.read(262144)
                payload = json.loads(error_bytes)
                error = payload.get("error", {})
                for name in ("code", "type", "failed_generation"):
                    if isinstance(error.get(name), str):
                        provider_failure[name] = error[name][:16000]
            except (ValueError, AttributeError):
                pass
            raise urllib.error.HTTPError(exc.url, exc.code, exc.reason, exc.headers,
                                         io.BytesIO(locals().get("error_bytes", b""))) from None
    for position, case in enumerate(cases):
        if position:
            time.sleep(args.delay)
        provider_failure.clear()
        hits = case["retrieved"] if args.failed_run else retriever.search(case["question"], k=4)
        row = {**case, "retrieved": hits}
        try:
            with patch("urllib.request.urlopen", observed_urlopen):
                raw = generator.generate(case["question"], hits)
            row["raw_model_output"] = raw
            try:
                row["validated_answer"] = validate_answer(raw, hits)
                row["status"] = "valid"
                row["refused"] = row["validated_answer"]["refused"]
            except AnswerValidationError as exc:
                row["status"] = "validation_failed"
                row["validation_reason"] = str(exc)
        except AnswerValidationError as exc:
            row["status"] = "validation_failed"
            row["validation_reason"] = str(exc)
            row["raw_model_output"] = getattr(generator, "last_raw_output", None)
        except ProviderError as exc:
            row["status"] = "provider_failed"
            row["app_status"] = exc.status
            row["error"] = str(exc)
            row["provider_diagnostic"] = dict(provider_failure)
        row["raw_provider_output"] = getattr(generator, "last_raw_output", None)
        row["response_format_recovered"] = getattr(generator, "response_format_recovered", False)
        row["provider_attempts"] = getattr(generator, "last_attempt_count", 1)
        if provider_failure:
            row["provider_diagnostic"] = dict(provider_failure)
        report["results"].append(row)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in row.items()
                          if k not in {"retrieved", "raw_model_output", "validated_answer", "provider_diagnostic", "raw_provider_output"}}), flush=True)
        if row.get("app_status") in (429, 503, 504):
            break
    print("Diagnostic saved: " + str(path), flush=True)
    print("No policy, prompt, retrieval setting, or original benchmark result was changed.", flush=True)


if __name__ == "__main__":
    main()
