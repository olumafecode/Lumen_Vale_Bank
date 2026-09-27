# Response-format repair after the first evaluation

The original run 20260927T210223Z-9a00acb7 remains unchanged: seven of 20 answerable requests succeeded, ten failed citation/answer validation, and three returned generic provider errors.

The separate development diagnostic 20260927T212309Z-3604257f reproduced a specific failure: D02+D03 returned a top-level list containing an answer object and a separate claim object. The validator correctly rejected this as Invalid answer structure. D01-control passed. D01+D05 was structurally valid but refused, so it is not evidence of successful compound-question coverage.

## Change

Generation now requests strict JSON Schema rather than generic JSON-object mode. The schema requires a single object, a boolean answerable field, and a claims array; every claim requires text and citations, and every citation requires a quote and a chunk ID from the actual retrieved set. Extra properties are disallowed at every object level.

Prompt/format identity is now policy-claims-v2-schema. The system prompt text, retrieval settings, original policies, and held-out questions are unchanged. The evaluator records the strict response-format setting in new runs.

The server still rejects fabricated quotes, missing citations, overly long answers, and invalid evidence. A schema validates structure, not factual entailment. This fix does not establish the cause of all ten validation failures or the three earlier provider errors. No partial malformed answer is salvaged or presented to the user.

Groq documents strict support for the configured openai/gpt-oss-20b model:
https://console.groq.com/docs/structured-outputs

## Verification

68 tests passed in 10.02 seconds, including a malformed-list regression, strict boolean types, retrieved-ID constraints, and continued rejection of an invented quote even when it matches the JSON schema.

Live verification is pending. Run:

    .\.venv\Scripts\python.exe -m scripts.diagnose_chat

The diagnostic now prints refused explicitly for structurally valid results. Keep its new uniquely named file alongside the first diagnostic. Check both schema compliance and answer support before deciding to rerun the benchmark.

Any repeat of the original benchmark after this repair must be labeled a benchmark-informed development rerun, not a new untouched held-out result. Retain the first-run failure measurements. Human review and final evaluation remain incomplete.
