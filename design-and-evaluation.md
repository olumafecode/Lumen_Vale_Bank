# Design and evaluation

## Implemented as of Stage 2

The application foundation uses Python 3.12, Flask, python-dotenv, and Waitress. An application factory separates configuration from routes and allows tests to use temporary source directories. The root WSGI entry point is `app.py`, compatible with the assignment's `python -c "import app"` startup check. Waitress supports the same launch command on Windows and Unix platforms, while binding only to localhost by default.

The 12 canonical Markdown files and their Stage 1 hashes are preserved. The verifier reads a manifest allowlist instead of recursively ingesting the repository, so evaluation answers cannot accidentally become source evidence. It validates count, identity uniqueness, contained paths, and content hashes. This is integrity checking, not ingestion. The PDF is a human-readable duplicate kept outside the canonical Markdown directory.

The health endpoint distinguishes a running foundation from a usable RAG service. It verifies the corpus for each request, returns 503 for invalid sources, and reports `rag_ready: false`. It does not contact a provider. No `/chat` route, model-generated answer, vector database, or fake response has been added at this stage.

## Planned choices to validate in Stage 3 and Stage 4

- Embeddings: local `sentence-transformers/all-MiniLM-L6-v2`, selected to avoid embedding API charges; pin a model revision and verify memory requirements during ingestion implementation.
- Chunking: heading-aware, approximately 180-220 embedding-token chunks with modest overlap and document/section metadata. Check the chosen tokenizer and model limit rather than assuming word count equals tokens.
- Vector store: local Chroma, subject to dependency/platform checks and resource testing. Persist it under ignored `data/index/` and make rebuilding explicit.
- Retrieval: initially top-k=4; compare alternatives using separate development questions before freezing evaluation.
- Generation: configurable free-tier provider, initially Groq with an OpenRouter option. Model IDs, quotas, and actual availability will be verified before use. No key is needed or loaded now.
- Citations and guardrails: answers must link to specific retrieved passages; unsupported questions abstain. Retrieved source text is evidence, not instructions. Validate returned citation IDs instead of trusting model text alone.

These packages and models have not been installed merely to fill a dependency list. They will be added to the pinned locks when the corresponding implementation is tested. The runtime lock currently contains only dependencies used by the Stage 2 code.

## Reproducibility decisions

Direct dependencies are recorded in `.in` files. Full transitive runtime and development requirements are pinned with package hashes. The project was verified using Python 3.12.14 on Windows; other OS installations are not claimed as tested. Source hashes, explicit file order in the future ingestion pipeline, fixed seeds for any applicable random sampling, versioned prompts, and model settings will be recorded as they are implemented.

Stage 2 seeds the standard-library random generator, although current routes and corpus checks do not sample randomly. Python hash randomization is controlled by setting `PYTHONHASHSEED` before process launch. Later numerical libraries require separate seeding. External LLM responses can still vary.

## Evaluation plan and status

The benchmark contains 20 answerable policy questions and five unsupported/adversarial cases, with five separate development prompts. The original scored questions and gold answers are preserved under `evaluation/`. They are not corpus inputs. The scoring plan defines strict end-to-end and answer-only groundedness and citation metrics with explicit denominators, preventing failures and refusals from silently inflating results.

Targets are groundedness >=90%, citation accuracy >=95%, answer coverage >=90%, guardrail correctness 5/5, and warm latency p50 <=5 seconds and p95 <=12 seconds across 20 requests. These are proposed targets, not achieved results. No RAG quality or model latency has been measured. Web startup checks are not RAG evaluation.

See `evaluation/success-criteria-and-scoring.md` for sampling, reviewer evidence, latency definitions, and handling failures. Actual Stage 2 environment and startup evidence is recorded separately in `docs/stage-2-verification.md`.
