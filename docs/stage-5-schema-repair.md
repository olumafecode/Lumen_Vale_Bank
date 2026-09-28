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

## Compound retrieval and bounded provider repair

The next live diagnostic (20260927T214407Z-c3c59e21) showed that strict schema mode alone did not resolve generation: Groq returned HTTP 400 with json_validate_failed and a list-shaped failed_generation. The other compound question lacked its privacy-deadline evidence, making refusal appropriate for the retrieved context.

Version policy-claims-v3-compound now retrieves independently for up to three explicit question parts, four chunks per part with deduplication and a 12-chunk maximum. Single questions retain their original hybrid retrieval. The prompt explicitly requires all claims in one object. A provider HTTP 400 json_validate_failed receives at most one formatting-repair retry with the same question/evidence and original safeguards. No failed_generation content is executed, adopted as an answer, or sent back as an instruction. Rate limits and other errors are not retried by this adapter. Client timing includes the provider retry; responses record provider_attempts.

72 automated tests passed. Real local retrieval now supplies both needed policy sections for each compound development prompt (eight chunks each); details are in stage-5-compound-retrieval.json. Live generation remains pending. These changes are benchmark-informed development; the initial benchmark and both diagnostics remain unchanged.

## Validated repair of the observed response envelope

The next diagnostic (20260927T215740Z-0e270a71) exhausted both format attempts for both compound prompts. Its provider errors contained the same exact malformed structure: a list whose first item is an answerable=true object with claims, followed by standalone claim objects.

Version policy-claims-v4-envelope-repair recognizes only that bounded shape, moves the standalone claims into the first claims list, and runs the existing validator before accepting the result. It does not modify claim text, quotes, or citation IDs; does not evaluate generated code; and rejects ambiguous shapes, extra fields, refusal envelopes, unknown citations, fabricated quotes, or excessive output. JSON parsing and input reads remain bounded. If recovery fails, the existing single formatting retry/error path applies. A recovered result is explicitly marked response_format_recovered=true; provider_attempts remains recorded. This supersedes the earlier decision to discard every malformed envelope.

Offline replay of both preserved failures now validates two claims and two citations per compound answer, without new provider calls. See stage-5-envelope-replay.json; it is not a new live run or a final human-scored result. 78 tests pass. Live verification is still pending, and all original benchmark/diagnostic records remain unchanged.
