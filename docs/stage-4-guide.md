# Stage 4: policy chat

Live Groq access is verified. The user-run smoke test returned five cited policy answers and a correct out-of-scope refusal; the injection probe initially received HTTP 429, then correctly refused the request on a separate retry (HTTP 200, 638.8 ms). No final answer-quality scores are claimed.

## Start in VS Code

Open this project's existing .env file and add these lines, replacing the placeholder locally:

    GROQ_API_KEY=your_key
    LLM_MODEL=openai/gpt-oss-20b

Get the key from https://console.groq.com/keys. Never paste it into chat, commit it, or copy it into .env.example. Free-plan quotas depend on the account; check the provider console. The app makes no paid fallback or automatic retry.

In a terminal at the project root:

    .\.venv\Scripts\python.exe -m scripts.serve

Open http://127.0.0.1:8000/. Stop an older server with Ctrl+C before restarting so it loads the current code and settings. Python 3.12.14, installed dependencies, and the local index already exist; no reinstall is needed.

Try an annual-leave question. Then try an unrelated question. Inspect the cited quotes and open their source links. Conversation history stays in the page only: every question is independent.

To run seven live development checks (five development questions plus two scope/injection probes):

    .\.venv\Scripts\python.exe -m scripts.smoke_chat

This sends questions and retrieved synthetic policy passages to Groq. It writes responses to ignored evaluation/runs/stage-4-live-smoke.json and stops early on access, quota, or connection errors. Review responses for support and correct refusals; HTTP success alone does not prove answer quality. The held-out 25-question benchmark is not read.

## What is implemented

- GET /: responsive chat, example questions, pending state, clear error feedback, and supporting snippets.
- POST /chat: JSON {"question":"..."}; returns answer, claim-to-citation mappings, source URLs, refusal flag, elapsed milliseconds, model, prompt version, and index fingerprint.
- GET /sources/<chunk_id>: escaped indexed passage, policy title, section, version, date, and line/page locator. No arbitrary filesystem paths are accepted.
- GET /health: corpus, index, model-cache/retriever readiness and provider configuration. rag_ready means local prerequisites and key presence, NOT a verified provider connection. The provider connection field explicitly says not_checked.

Questions are limited to 1,200 characters and 256 embedding tokens. Requests are limited to 16 KiB. Generated factual text is limited to 180 words and five claims. One inference request runs at a time in this local process; concurrent requests receive HTTP 429. Provider requests time out after 30 seconds. Errors do not expose raw provider payloads or secrets.

## Retrieval and guardrails

The 106 original Chroma chunks are unchanged. Hybrid retrieval fuses top-20 dense and BM25 rankings with reciprocal rank fusion (constant 60), then supplies four passages to generation. BM25 uses indexed passage text and source titles only. No evaluation answers enter the source index.

The system prompt treats the question and passages as untrusted data, limits answers to the fictional policies, and requests abstention when evidence is insufficient. Each claim must reference retrieved chunk IDs and exact supporting quotes. Server validation rejects unknown IDs, invented quotes, missing citations, excessive output, and malformed results. Source changes during generation block the answer. Model text is rendered as text, never HTML.

These are basic guardrails, not proof of semantic entailment or immunity to prompt injection. A genuine quotation could still be paired with an unsupported claim. Human groundedness/citation review and adversarial evaluation remain necessary in Stage 5. Invalid output returns a clear 502 error instead of presenting an unverified answer.

## Verified results

- 58 automated tests passed, including existing ingestion tests, citation rejection, input validation, missing keys, model timeout/quota/access errors, source changes, and HTML escaping.
- Real hybrid retrieval on five development prompts: any-expected-section hit rate 100% versus dense-only 80%; mean expected-section recall 90% versus 70%.
- D02 still misses one of two expected sections. This small development sample is not a final benchmark.
- Browser preview checked: layout, example-question selection, submission, missing-key error, and restored question text.
- Live smoke run: D01–D05 returned cited policy answers (HTTP 200); the recipe request was refused. Successful requests took 486.4–702.8 ms. The injection probe initially hit HTTP 429; its isolated retry returned HTTP 200 with refused=true in 638.8 ms. Both attempts are preserved.
- Final benchmark groundedness/citation accuracy and p50/p95 answer latency: NOT_RUN.

The completed isolated retry used:

    .\.venv\Scripts\python.exe -m scripts.smoke_chat --case injection-probe

This saves stage-4-live-smoke-injection-probe.json separately, preserving the original run. If it receives another 429, allow more time for the quota to reset; no automatic retries or paid fallback are used.

The app is a local academic demo. Public hosting, authentication, deployment-level rate limiting, and CI are later-stage work.

## Provider references

Checked against current provider documentation; model access can change:

- https://console.groq.com/docs/deprecations
- https://console.groq.com/docs/structured-outputs
- https://console.groq.com/docs/api-reference
- https://console.groq.com/docs/rate-limits

The older llama-3.3-70b-versatile free/developer option was retired. The configurable default is openai/gpt-oss-20b through Groq's chat-completions endpoint; no OpenAI API key is used.
