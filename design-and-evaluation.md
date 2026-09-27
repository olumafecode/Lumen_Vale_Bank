# Design and evaluation

## Implemented through Stage 3

Python 3.12, Flask, python-dotenv, and Waitress provide the application foundation. The app factory separates configuration from routes and supports temporary test directories. The app.py WSGI entry point supports the assignment's import/start check. Waitress binds to localhost by default.

The manifest is an explicit allowlist. All 12 original Markdown documents retain their Stage 1 hashes. The duplicate review PDF and evaluation documents are excluded from ingestion. Parsing supports Markdown, HTML, UTF-8 TXT, and text-based PDF; PDF pages without extractable text require OCR or review. Metadata preserves document/section identity, source hashes, line or page locators, and normalized character offsets.

Heading-aware chunks never cross sections. The actual MiniLM tokenizer bounds each embedding input, including its title and heading, to 220 tokens with approximately 30 tokens of overlap inside a section. This respects the model's 256-token limit without silent truncation. The corpus produces 106 chunks from 104 subsections.

Chroma's CPU ONNX all-MiniLM-L6-v2 implementation supplies local 384-dimensional embeddings without a paid API or PyTorch. A pinned archive SHA-256 and component hashes verify the model cache. Chroma stores explicit vectors, passages, and metadata using cosine distance. This lightweight local design suits the small corpus; hosting memory and startup constraints remain to be measured.

Stable chunk IDs and a configuration/source fingerprint identify each index snapshot. A build lock prevents concurrent writers; a completed collection is verified before the active-index record is atomically published. Unchanged builds reuse the same collection. Source changes invalidate readiness. Previous collections remain available until intentional cleanup.

Terminal retrieval returns top-k passages (default 4), distances, and source metadata. Distances are similarity measurements, not calibrated confidence. Health reports corpus and index readiness separately and keeps rag_ready false until generation is implemented.

See [Stage 3 guide](docs/stage-3-guide.md) for technical references and [verification](docs/stage-3-status.md) for measured evidence.

## Stage 4 design work

Integrate a configurable generation provider after checking actual model availability and quotas. Add the chat UI, POST /chat, linked source snippets, output limits, and scope refusal. Treat retrieved text as evidence rather than instructions and validate returned citation IDs against retrieved passages. A relevant-looking retrieval result alone does not establish that the evidence answers the question.

The development baseline missed the administrator-account rule and one of two manual-adjustment sections. Compare retrieval improvements using development cases before freezing the scored evaluation. Do not silently increase reported performance by reusing held-out gold answers during tuning.

## Reproducibility

Direct dependencies live in .in files; full transitive runtime and development locks include exact versions and artifact hashes. Ordinary setup installs these locks without resolving new versions. Model preparation is explicit; cached build/search require no external API. The verified environment is Windows with Python 3.12.14; other platforms have not been validated.

Source ordering, tokenizer windows, chunk IDs, model bytes, dependency versions, and index fingerprints are recorded. The random seed defaults to 42; set PYTHONHASHSEED before launch. Current ingestion has no random sampling. Fixed seeds do not guarantee identical approximate nearest-neighbor results or external LLM outputs across platforms.

## Evaluation plan and results so far

The held-out benchmark contains 20 answerable questions and five unsupported/adversarial cases. Five development prompts are separate. None of these files is ingested. The scoring plan specifies denominators and handling of failures and refusals.

Proposed final targets: groundedness >=90%, citation accuracy >=95%, answer coverage >=90%, guardrail correctness 5/5, and warm request-to-answer latency p50 <=5 seconds and p95 <=12 seconds across 20 requests. These targets have not been demonstrated.

The Stage 3 development run at k=4 achieved 80% any-expected-section hit rate and 70% mean per-question expected-section recall. These are retrieval-only baseline metrics on five prompts, not answer-quality scores or final latency results. Full test suite: 34 passed, zero skipped.

See evaluation/success-criteria-and-scoring.md for the final scoring protocol. Preserve actual outputs and reviewer judgments when the complete application is evaluated.

## Stage 4 implementation

Hybrid BM25/dense retrieval at k=4 improves the five development prompts to 100% any-section hit rate and 90% mean expected-section recall. The Groq adapter requests JSON claims and exact evidence quotes; the server validates citations and limits output to 180 words. These checks do not establish semantic support. Chat and source routes are implemented, with 58 automated tests passing. Live provider checks remain pending local key setup. See docs/stage-4-guide.md for configuration, error behavior, and limitations.

### Live development verification

The user-run Groq checks returned five cited policy answers and a correct out-of-scope refusal. The injection probe initially hit HTTP 429, then returned a correct refusal in an isolated retry (HTTP 200; 638.8 ms). Evidence is preserved in docs/stage-4-live-smoke-initial.json and docs/stage-4-live-smoke-injection-probe.json. These development checks establish working provider integration and the observed refusal behavior; they do not replace the held-out Stage 5 evaluation.

## Stage 5 measurement implementation

The evaluator freezes code and benchmark hashes and sends only question text to a private local HTTP server. It captures the exact retrieved passages for each generation attempt without passing gold answers to retrieval or generation. One warm-up is excluded, Q01–Q20 provide warm client latency, and all 25 cases are preserved for quality/guardrail review. Rate-limit retries and their waits are included in request duration; 30-second between-case pacing is excluded. Semantic scores require a completed human review CSV; the report otherwise explicitly marks review pending. See docs/stage-5-guide.md. No live held-out score has been claimed at implementation time.
