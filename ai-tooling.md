# AI tooling disclosure

OpenAI Codex assisted with planning, synthetic policy drafting, repository setup, code, documentation, dependency locking, and local verification for this project.

## Stage 1

Codex drafted the fictional Lumen Vale Bank profile and eleven policies, the corpus manifest, the review PDF, evaluation questions with reference passages, and the scoring plan. The policy facts, currency, contact routes, and deadlines are invented. No real bank policies or private records were supplied or copied. Automated checks verified counts, source references, evidence quotes, and hashes; the rendered PDF was visually inspected.

## Stage 2

Codex created the Flask foundation, configuration loading, corpus-integrity verifier, setup/run commands, dependency locks, and focused tests. Packages were installed in an isolated Python 3.12 environment. Real startup and HTTP checks were performed and recorded in `docs/stage-2-verification.md`. The local Git repository was initialized without publishing to GitHub.

AI assistance worked well for producing consistent document structures and writing repeatable integrity checks. Tool execution still required verification: the system default was Python 3.14, so a separate available Python 3.12 runtime was selected; the dependency locker's default cache location was not writable in the workspace permissions, so caching was redirected into ignored project storage. A PowerShell setup helper could not run under the machine's execution policy, so it was replaced with a Python helper and verified without changing that policy. These issues were resolved before claiming setup success.

## Human responsibility and remaining work

The student should review and understand the fictional policy choices, inspect generated code, make any desired edits, and accurately disclose assistance in the final submission. Drafting and passing tests do not establish legal fitness, complete application correctness, or achieved RAG performance. No model-based evaluation scores, deployment, recorded demo, or final submission have been fabricated. Update this file as later stages are completed, including what worked, limitations, and meaningful human changes.
