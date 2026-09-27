# AI tooling disclosure

OpenAI Codex assisted with planning, synthetic policy drafting, repository setup, code, documentation, dependency locking, and local verification for this project.

## Stage 1

Codex drafted the fictional Lumen Vale Bank profile and eleven policies, the corpus manifest, the review PDF, evaluation questions with reference passages, and the scoring plan. The policy facts, currency, contact routes, and deadlines are invented. No real bank policies or private records were supplied or copied. Automated checks verified counts, source references, evidence quotes, and hashes; the rendered PDF was visually inspected.

## Stage 2

Codex created the Flask foundation, configuration loading, corpus-integrity verifier, setup/run commands, dependency locks, and focused tests. Packages were installed in an isolated Python 3.12 environment. Real startup and HTTP checks were performed and recorded in `docs/stage-2-verification.md`. The local Git repository was initialized without publishing to GitHub.

AI assistance worked well for producing consistent document structures and writing repeatable integrity checks. Tool execution still required verification: the system default was Python 3.14, so a separate available Python 3.12 runtime was selected; the dependency locker's default cache location was not writable in the workspace permissions, so caching was redirected into ignored project storage. A PowerShell setup helper could not run under the machine's execution policy, so it was replaced with a Python helper and verified without changing that policy. These issues were resolved before claiming setup success.

## Stage 3

Codex implemented document parsers, tokenizer-bounded chunking, local ONNX MiniLM embeddings, versioned Chroma indexing, terminal search, and focused tests. The student ran the dependency/model setup command in VS Code because package downloads were blocked in the agent runtime. Codex then verified the actual model and index, unchanged-build reuse, 34 passing tests, and five development retrieval prompts. The baseline retrieved an expected section for 4/5 prompts; misses are recorded rather than presented as successful answers. The held-out final answer benchmark was not run or used to tune this stage.

## Human responsibility and remaining work

The student should review and understand the fictional policy choices, inspect generated code, make any desired edits, and accurately disclose assistance in the final submission. Drafting and passing tests do not establish legal fitness, complete application correctness, or achieved RAG performance. No model-based evaluation scores, deployment, recorded demo, or final submission have been fabricated. Update this file as later stages are completed, including what worked, limitations, and meaningful human changes.

## Stage 4

Codex implemented hybrid retrieval, the Groq adapter, claim/citation validation, chat and source routes, the web interface, development checks, and tests. The actual development retrieval comparison improved any-section hit rate from 80% to 100% and mean expected-section recall from 70% to 90%. The browser missing-key path was inspected. Provider behavior in automated tests uses explicit test doubles; no live generation success or final answer-quality result is claimed without the student's local provider setup.

## Stage 5 tooling

Codex implemented held-out evaluation, loopback HTTP timing, source-evidence capture, immutable run directories, human-review packets, explicit quality denominators, and nearest-rank latency reporting. Focused tests verify the scoring and record-preservation behavior with test doubles. The student must run the live benchmark in their terminal because the agent network runtime cannot reach Groq, and must review semantic judgments before reporting final human-reviewed scores. Gold answers are review-only and never supplied to the RAG application.

### Post-benchmark diagnosis

A user-run development diagnostic captured a malformed list where the answer object was required. Codex switched generation to strict provider JSON Schema, constrained citation IDs to retrieved evidence, preserved quote checks, and added regression tests (68 tests passed). The original evaluation and diagnostic are retained. This is a benchmark-informed repair, not an independent new held-out result; live re-verification and human semantic review are still required.
