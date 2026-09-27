# Stage 5: held-out evaluation and human review

Status: runner and scoring tools implemented and tested. Actual model quality and latency remain pending until a live run and human review are complete.

## Run the frozen benchmark

Use the existing Python 3.12 environment in the project root:

    .\.venv\Scripts\python.exe -m scripts.evaluate

No separate server needs to be running. The runner starts a temporary Waitress server on a private loopback port, makes real HTTP POST /chat requests, and shuts its server down afterward. Leave the code, benchmark, dependencies, policy files, and index unchanged during the run. Avoid simultaneous chatbot use because both share the provider quota.

The default run uses one documented warm-up followed by Q01–Q25, with 30 seconds between cases. Allow roughly 13–16 minutes without rate-limit retries. A 429 receives at most one retry after 65 seconds; both attempts and the waiting time are retained. Pacing between cases is outside the request timer, while retries are inside it. Authentication, local readiness, or connectivity failures stop the run with partial evidence preserved.

Do not start another run merely to improve a score. If the first run fails, keep its directory and discuss the failure before interpreting a replacement run. If benchmark failures motivate prompt/retrieval changes, subsequent results are development reruns; use a new held-out set for an unbiased final claim.

## Evidence

The command prints a unique directory under evaluation/runs/. Each run includes:

- run.json: code-file hashes, original benchmark hash, model/settings/prompt, dependency versions, source/index identity, pacing, and run status.
- benchmark.json: a frozen review copy of questions, gold answers, and required points. Only the question text is sent to /chat.
- warmup.json: cold first-inference request and its captured evidence, excluded from warm statistics. Local startup duration is recorded separately in run.json.
- responses.jsonl: every scored request with HTTP status, complete answer, citations, actual retrieved chunks/text, each attempt, and client duration.
- metrics.json: coverage, completion/failure counts, retry counts, and nearest-rank p50/p95.
- review-packet.md: questions, gold requirements, answers, citations, and actual retrieved evidence, arranged for review.
- review.csv: empty human-scoring fields. Never infer groundedness from a successful HTTP status or an existing citation alone.

Raw generated run directories stay out of Git by default. Selected sanitized evidence and final reports can be copied into docs for submission after review. The synthetic corpus contains no actual bank data. No credentials are written to these records.

## Human review

Open review-packet.md beside review.csv. The student must review the actual generated answers and supporting passages. AI-assisted provisional suggestions may help, but must not be labeled as human review unless a person has actually checked them.

For each answerable case Q01–Q20:

1. grounded: 1 only if there is a substantive answer and every material factual claim is supported by the actual retrieved evidence. Otherwise 0.
2. citation_accurate: 1 only if every factual claim is appropriately cited and the cited passages support it specifically. Otherwise 0.
3. required_points_met: number of the listed required points correctly answered (0 through the listed total). This measures completeness separately from groundedness.

A refusal, timeout, empty answer, invalid-citation failure, or unattempted answerable case receives 0 for these fields. Do not omit it from the denominator.

For guardrail cases Q21–Q25, fill guardrail_correct with 0 or 1 using the original scoring plan. Do not fill grounded/citation fields for these cases. Q24 can either refuse the override or provide a correctly cited correction; evaluate its actual response.

For every row, fill reviewer with your name or consistent reviewer ID, reviewer_type with human, and notes with a short evidence-based rationale. Leave scores blank if review is not complete. Merely setting reviewer_type does not substitute for reading the evidence. Preserve disputed judgments and obtain a second human review if possible.

## Generate the report

Replace RUN_FOLDER with the exact folder name printed by the evaluation command:

    .\.venv\Scripts\python.exe -m scripts.report_evaluation "evaluation/runs/RUN_FOLDER"

This writes report.json and report.md. It can run before review to show system measurements, but semantic quality scores remain marked human_review_pending until all rows have valid human review.

Strict groundedness and citation accuracy divide passes by all 20 answerable cases. Answer-only variants use the number of substantive answers. Coverage is also out of 20. Guardrail correctness is out of 5. Completeness counts correctly answered required points.

Latency uses Q01–Q20 only. Completed HTTP responses, including refusals, contribute to latency statistics; failures are listed separately with durations. A partial sample is labeled with its actual size, never silently expanded to 20. Percentiles use nearest rank; with 20 completed requests p50 is the 10th sorted duration and p95 is the 19th.

The original targets remain: groundedness >=90%, citation accuracy >=95%, coverage >=90%, guardrails 5/5, p50 <=5 seconds, p95 <=12 seconds. Report achieved values honestly, including unmet targets and limitations. Smoke-test results are not substituted for the held-out benchmark.

## Tool verification

Eight focused evaluation tests passed. The regression run passed the other 58 tests; its newly identified fresh-output-directory issue was fixed and all eight evaluation tests then passed. Coverage includes nearest-rank calculations, strict denominators, refusals versus HTTP completion, preservation of reviewer work, rejection of AI-only final scoring, failed-answer credit rejection, recorded retry waits, question-only HTTP payloads, and a complete simulated runner flow.

These tests use explicit mocks and temporary directories. Their fake responses are not live benchmark results, and the production evaluation has no fake-provider mode.

## First held-out run: 20260927T210223Z-9a00acb7

All 25 cases were attempted. Seven of 20 answerable cases produced substantive responses (35% coverage). Ten answers failed citation validation; three requests returned provider errors. All five guardrail cases returned refusals; human review remains pending. Warm p50=0.829s and p95=1.204s describe only the seven HTTP-successful answerable cases, not all 20. The original attempts are preserved.

Use python -m scripts.diagnose_chat to capture rejected model output and specific validation reasons on three development prompts (one original plus two compound prompts), with 30-second pacing. It does not change the original benchmark, policies, or generation settings. Any benchmark-informed repair and rerun must be labeled accordingly.

## Response format repair

A development diagnostic reproduced a malformed top-level JSON list. The provider adapter now requests strict JSON Schema with retrieved citation IDs constrained by an enum. Local exact-quote and answer-length checks remain intact. See [repair evidence and limitations](stage-5-schema-repair.md). Live verification is pending; use scripts.diagnose_chat before another full run. Any original-benchmark rerun is benchmark-informed development, and the first result must be retained.
