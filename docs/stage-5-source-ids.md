# Source-ID generation contract

The diagnostic diagnostic-20260928T050642Z-5ad217e1 reproduced concrete failures: Q01 joined nonadjacent source sentences into one quote; Q08 and Q05 changed ordinary hyphens to nonbreaking hyphens; Q06 and Q10 had malformed nested JSON. Q13 stopped on a provider token-rate limit. These observations apply to the diagnostic, not necessarily to every original failed output, which was not recorded.

Prompt version policy-claims-v5-source-ids replaces model-generated quotations and long chunk hashes with short request-local evidence IDs. The wire format is one object with a claims array; each claim has text and a sources array. An empty claims array means refusal. There are no nested citation objects or separate answerable flag in the provider schema.

The application resolves each selected ID to its original retrieved chunk, attaches that complete passage, then applies the existing validator. Unknown IDs, model-supplied quote fields, missing citations, excessive claims, and answers over 180 words are rejected. Passage whitespace is normalized by the existing validator; punctuation and wording are not rewritten. Source links and document/section metadata retain their existing API format. The old envelope repair helper remains for offline historical records but is no longer used by the live provider adapter.

Citations are now longer chunk-level passages rather than model-selected excerpts. Selecting a real source does not prove that a claim follows from it: human groundedness and citation-accuracy review remains required. No quality improvement is claimed from mocked tests, and no original evaluation record is replaced. This is benchmark-informed development.

The provider keeps at most one retry for HTTP 400 json_validate_failed within the existing timeout budget. Failed provider generations are not salvaged. Rate limits are returned explicitly; longer diagnostic spacing can reduce per-minute pressure but cannot guarantee quota availability.

After CI passes, use a targeted replay with 65-second spacing:

~~~powershell
.\.venv\Scripts\python.exe -m scripts.diagnose_chat --failed-run evaluation/runs/20260928T044244Z-5666cfea --delay 65
~~~

Allow the previous token-limit window to reset first. If 429 repeats, stop and check the provider quota before making more requests. This script produces a new labeled diagnostic and does not update benchmark scores. Run the regular development/refusal smoke checks after the targeted diagnostic succeeds and before the next full evaluation.

Validation: 87 automated tests passed locally, including multi-source mapping, exact source attachment, refusal, source-ID rejection, output limits, and bounded retries. Live provider behavior and hosted CI remain to be verified.
