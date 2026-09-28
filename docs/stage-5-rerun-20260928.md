# Benchmark-informed rerun: 20260928T044244Z-5666cfea

This is a development rerun after fixes informed by the initial benchmark. It is not a new untouched held-out evaluation. The initial run 20260927T210223Z-9a00acb7 and the new raw run remain unchanged.

- Answerable requests: 14/20 substantive answers (70% coverage), up from 7/20 (35%).
- Failed answerable requests: 6/20 (30%).
- Guardrail questions: all five returned refusals. Refusal behavior is not a groundedness score.
- Successful-answer latency, n=14, nearest-rank: p50 1.377 seconds; p95 2.829 seconds. These percentiles exclude the six failed requests and the separate guardrail cases.
- Four provider-format retries were recorded; no evaluator rate-limit retries occurred.
- Groundedness and citation accuracy remain pending human review.

## Remaining errors

Q01, Q08, Q10, and Q13 returned the application's generic answer/citation validation error. This message can represent structural, output-length, or citation problems; it does not prove that all four had incorrect quotations. Q05 and Q06 returned generic provider errors after two provider attempts. The saved benchmark does not contain raw rejected model output or the precise validator/provider reasons, so the underlying causes are not yet established.

## Targeted diagnosis

The diagnostic supports an explicit failure-replay mode. It selects only non-200 requests from the saved run and passes only their questions and saved retrieved passages to generation. Gold answers and expected evidence are not supplied to the generator. It writes a separate uniquely named diagnostic labeled benchmark-informed, never overwriting the run or counting successful replays as benchmark results. The original prompt, validator, corpus, and retrieval implementation are unchanged by this diagnostic addition.

Run after pushing and checking GitHub Actions:

~~~powershell
.\.venv\Scripts\python.exe -m scripts.diagnose_chat --failed-run evaluation/runs/20260928T044244Z-5666cfea
~~~

This makes live provider requests, spaced 30 seconds apart, and captures selected provider error fields, raw model output when returned, and precise validation reasons. It does not record request authorization headers. Model outputs can vary on replay; this cannot reconstruct the original missing outputs. Review the new diagnostic before changing safeguards or running another full benchmark.

Local validation: 80 tests passed, including failure selection, frozen-evidence use, exclusion of gold answers, preservation of saved responses, and rejection of missing evidence. One local pytest cache-permission warning did not affect the tests. Live replay and GitHub Actions for this change remain pending.
