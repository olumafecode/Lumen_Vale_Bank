# Policy assistant evaluation

Run: 20260927T210223Z-9a00acb7 (complete)
Model: openai/gpt-oss-20b | prompt: policy-claims-v1

## System results

- Answerable cases attempted: 20/20
- Completed HTTP responses: 7/20
- Substantive answer coverage: 7/20
- Warm p50: 0.829 seconds
- Warm p95: 1.204 seconds
- Percentile sample: 7 completed HTTP responses (including refusals)
- 429 retries included in durations: 0

Failed requests: [{"id": "Q01", "status": 502, "seconds": 0.8845915000420064}, {"id": "Q03", "status": 502, "seconds": 0.8339078999706544}, {"id": "Q05", "status": 502, "seconds": 0.9896387999760918}, {"id": "Q06", "status": 502, "seconds": 0.9796954999910668}, {"id": "Q07", "status": 502, "seconds": 1.1694960999884643}, {"id": "Q08", "status": 502, "seconds": 0.9868266000412405}, {"id": "Q09", "status": 502, "seconds": 1.2219806000357494}, {"id": "Q11", "status": 502, "seconds": 0.9226066999835894}, {"id": "Q13", "status": 502, "seconds": 0.7757309000007808}, {"id": "Q16", "status": 502, "seconds": 1.1135440000216477}, {"id": "Q18", "status": 502, "seconds": 0.7639323999756016}, {"id": "Q19", "status": 502, "seconds": 0.8748027999536134}, {"id": "Q20", "status": 502, "seconds": 1.1599538999726065}]

Warm-up excluded; pacing outside timers; retries inside timers. Nearest-rank percentiles.

## Quality review

{
  "status": "human_review_pending",
  "pending_ids": [
    "Q01",
    "Q02",
    "Q03",
    "Q04",
    "Q05",
    "Q06",
    "Q07",
    "Q08",
    "Q09",
    "Q10",
    "Q11",
    "Q12",
    "Q13",
    "Q14",
    "Q15",
    "Q16",
    "Q17",
    "Q18",
    "Q19",
    "Q20",
    "Q21",
    "Q22",
    "Q23",
    "Q24",
    "Q25"
  ],
  "note": "No semantic scores calculated from incomplete or AI-only review."
}

Targets: strict groundedness >=90%; strict citation accuracy >=95%; coverage >=90%; guardrails 5/5; warm p50 <=5s and p95 <=12s.
Incomplete runs or missing human review do not establish achieved final quality.
Preserve raw attempts, including failures, and disclose any benchmark-informed reruns.
