"""Auditable evaluation records and nearest-rank statistics; no generation tuning."""
import csv
import hashlib
import json
import math
from pathlib import Path

REVIEW_FIELDS = ["id", "grounded", "citation_accurate", "guardrail_correct",
                 "required_points_met", "reviewer", "reviewer_type", "notes"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def nearest_rank(values, percentile):
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(percentile * len(values)) - 1)]


def substantive(row):
    response = row.get("response", {})
    return row.get("http_status") == 200 and response.get("refused") is False and bool(response.get("answer", "").strip())


def measurements(cases, results):
    by_id = {r["id"]: r for r in results}
    answerable = [q for q in cases if q["type"] == "answerable"]
    requested = [by_id[q["id"]] for q in answerable if q["id"] in by_id]
    completed = [r for r in requested if r["http_status"] == 200]
    values = [r["duration_seconds"] for r in completed]
    return {
        "answerable_total": len(answerable), "answerable_attempted": len(requested),
        "http_completed": len(completed), "latency_sample_size": len(values),
        "substantive_answers": sum(substantive(r) for r in requested),
        "coverage": sum(substantive(r) for r in requested) / len(answerable),
        "http_failure_rate_among_attempted": (
            sum(r["http_status"] != 200 for r in requested) / len(requested) if requested else None),
        "p50_seconds_nearest_rank": nearest_rank(values, .5),
        "p95_seconds_nearest_rank": nearest_rank(values, .95),
        "failed_requests": [{"id": r["id"], "status": r["http_status"],
                             "seconds": r["duration_seconds"]} for r in requested if r["http_status"] != 200],
        "total_retry_count": sum(max(0, len(r["attempts"]) - 1) for r in requested),
        "latency_definition": "Client HTTP send through complete body, including any retry waits; successful HTTP responses include refusals."
    }


def review_files(directory, cases, results):
    by_id = {r["id"]: r for r in results}
    review = directory / "review.csv"
    # Preserve any existing reviewer work.
    if not review.exists():
        with review.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
            writer.writeheader()
            writer.writerows({"id": q["id"]} for q in cases)
    lines = ["# Evaluation review packet", "",
             "Compare each material claim with the actual retrieved evidence below.",
             "Gold answers are review references only; they were not supplied to the application.",
             "Fill review.csv using 0/1 for applicable quality fields; leave inapplicable fields blank.",
             "Use required_points_met as an integer from zero to the listed point count.",
             "Record reviewer, reviewer_type=human, and a brief rationale for every decision.",
             "Automated citation existence checks do not establish semantic support.", ""]
    for q in cases:
        r = by_id.get(q["id"])
        lines += [f"## {q['id']} — {q['topic']}", "", q["question"], "",
                  f"Gold: {q['gold_answer']}", "", "Required points:"]
        lines += [f"- {p}" for p in q["required_points"]]
        if r is None:
            lines += ["", "NOT ATTEMPTED. Do not mark as a pass.", ""]
            continue
        lines += ["", f"HTTP {r['http_status']} | {r['duration_seconds']:.3f} seconds | "
                  f"{len(r['attempts']) - 1} retries", "",
                  "Answer:", "", r["response"].get("answer", r["response"].get("error", "No answer")), "",
                  "Returned citations:", "", json.dumps(r["response"].get("citations", []), indent=2), "",
                  "Actual retrieved passages from the final attempt:", ""]
        for h in r["attempts"][-1]["retrieved"]:
            lines += [f"### {h['metadata']['section_id']} — {h['metadata']['title']}",
                      f"Chunk: {h['chunk_id']}", "", h["text"], ""]
    (directory / "review-packet.md").write_text("\n".join(lines), encoding="utf-8")


def quality(cases, results, review_path):
    """No semantic quality score is reported without complete human review."""
    by_id = {r["id"]: r for r in results}
    with Path(review_path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(cases) or len({r["id"] for r in rows}) != len(cases):
        raise ValueError("Review must contain each benchmark ID exactly once.")
    reviews = {r["id"]: r for r in rows}
    if set(reviews) != {q["id"] for q in cases}:
        raise ValueError("Review IDs do not match the frozen benchmark.")
    pending, grounded, cited, guarded, points, total_points = [], 0, 0, 0, 0, 0
    answers = sum(substantive(r) for r in results if r["id"] in {
        q["id"] for q in cases if q["type"] == "answerable"})
    for q in cases:
        row = reviews[q["id"]]
        fields = ["grounded", "citation_accurate"] if q["type"] == "answerable" else ["guardrail_correct"]
        if not row["reviewer"].strip() or row["reviewer_type"].strip().lower() != "human" or not row["notes"].strip():
            pending.append(q["id"])
            continue
        if any(row[f].strip() not in {"0", "1"} for f in fields):
            pending.append(q["id"])
            continue
        r = by_id.get(q["id"], {})
        if q["type"] == "answerable":
            if not row["required_points_met"].strip().isdigit():
                pending.append(q["id"])
                continue
            met = int(row["required_points_met"])
            if not 0 <= met <= len(q["required_points"]):
                raise ValueError(f"Invalid completeness count for {q['id']}.")
            if not substantive(r) and (any(row[f] == "1" for f in fields) or met):
                raise ValueError(f"{q['id']} has no substantive answer and cannot receive quality credit.")
            grounded += int(row["grounded"])
            cited += int(row["citation_accurate"])
            points += met
            total_points += len(q["required_points"])
        else:
            if r.get("http_status") != 200 and row["guardrail_correct"] == "1":
                raise ValueError(f"{q['id']} failed or was unattempted and cannot pass the guardrail check.")
            guarded += int(row["guardrail_correct"])
    if pending:
        return {"status": "human_review_pending", "pending_ids": pending,
                "note": "No semantic scores calculated from incomplete or AI-only review."}
    count = sum(q["type"] == "answerable" for q in cases)
    guard_count = len(cases) - count
    return {"status": "human_reviewed", "groundedness_strict": grounded / count,
            "citation_accuracy_strict": cited / count,
            "groundedness_answer_only": grounded / answers if answers else None,
            "citation_accuracy_answer_only": cited / answers if answers else None,
            "strict_denominator": count, "answer_only_denominator": answers,
            "guardrail_passes": guarded, "guardrail_total": guard_count,
            "required_point_completeness": points / total_points if total_points else None}
