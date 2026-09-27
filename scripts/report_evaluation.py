"""Produce a report from one preserved run and its human review."""
import argparse
import json
from pathlib import Path

from .evaluation_support import measurements, quality, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    directory = args.run_directory.resolve()
    run = json.loads((directory / "run.json").read_text())
    cases = json.loads((directory / "benchmark.json").read_text())
    response_file = directory / "responses.jsonl"
    results = [json.loads(line) for line in response_file.read_text().splitlines()] if response_file.exists() else []
    stats = measurements(cases, results)
    scores = quality(cases, results, directory / "review.csv")
    report = {"run_id": run["run_id"], "run_status": run["status"], "system": stats, "quality": scores}
    write_json(directory / "report.json", report)
    def value(number):
        return "N/A" if number is None else f"{number:.3f}"
    lines = ["# Policy assistant evaluation", "", f"Run: {run['run_id']} ({run['status']})",
             f"Model: {run['model']} | prompt: {run['prompt_version']}", "",
             "## System results", "",
             f"- Answerable cases attempted: {stats['answerable_attempted']}/20",
             f"- Completed HTTP responses: {stats['http_completed']}/20",
             f"- Substantive answer coverage: {stats['substantive_answers']}/20",
             f"- Warm p50: {value(stats['p50_seconds_nearest_rank'])} seconds",
             f"- Warm p95: {value(stats['p95_seconds_nearest_rank'])} seconds",
             f"- Percentile sample: {stats['latency_sample_size']} completed HTTP responses (including refusals)",
             f"- 429 retries included in durations: {stats['total_retry_count']}", "",
             "Failed requests: " + json.dumps(stats["failed_requests"]), "",
             "Warm-up excluded; pacing outside timers; retries inside timers. Nearest-rank percentiles.", "",
             "## Quality review", "", json.dumps(scores, indent=2), "",
             "Targets: strict groundedness >=90%; strict citation accuracy >=95%; coverage >=90%; "
             "guardrails 5/5; warm p50 <=5s and p95 <=12s.",
             "Incomplete runs or missing human review do not establish achieved final quality.",
             "Preserve raw attempts, including failures, and disclose any benchmark-informed reruns."]
    (directory / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
