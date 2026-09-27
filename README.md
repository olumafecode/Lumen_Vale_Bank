# Lumen Vale Bank Policy Assistant

A staged Master's-level AI engineering project: a retrieval-augmented generation (RAG) assistant for a **fictional bank's company policies**.

**Current status: Stage 4 complete; live development smoke checks verified.** Chat, hybrid retrieval, linked sources, and citation validation are available. The five development policy questions and both refusal probes completed successfully across the initial run and a rate-limit retry. See [Stage 4 setup and verification](docs/stage-4-guide.md).

## Quick start on Windows

Use **Python 3.12**; this project was verified with **3.12.14**. Run commands from this repository's root. A prepared `.venv` already exists in the local working copy; downloaded ZIPs intentionally exclude it.

For a fresh checkout with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.txt
Copy-Item .env.example .env
$env:PYTHONHASHSEED = '42'
.\.venv\Scripts\python.exe -m scripts.verify_corpus
.\.venv\Scripts\python.exe -m scripts.prepare_model
.\.venv\Scripts\python.exe -m scripts.build_index
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.serve
```

If `.env` already exists, keep it instead of copying over it. Environment activation is optional; all commands explicitly use the virtual environment. The development requirements include the runtime requirements, pytest, and pinned dependency-locking tools.

Alternatively, use the Python helper, which preserves an existing `.env`:

```powershell
py -3.12 -m scripts.bootstrap
```

If Python 3.12 is available at an explicit path rather than through the Python launcher:

```powershell
& 'C:\Path\To\Python312\python.exe' -m scripts.bootstrap
```

The helper is Python-based and needs no PowerShell execution-policy change. The local Stage 2 environment was created from the available bundled Python 3.12.14, because this computer's default `python` is 3.14. Do not recreate it with the default interpreter unintentionally.

Open **http://127.0.0.1:8000/**. The page provides the policy chat interface. **http://127.0.0.1:8000/health** returns JSON with corpus verification and RAG readiness. Press Ctrl+C in the server terminal to stop it. If port 8000 is occupied, change `APP_PORT` in `.env` and restart.

## macOS/Linux setup

The code and pinned packages are intended to be portable; this project was validated on Windows, not on a Linux/macOS host.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.txt
# Copy only when .env does not already exist.
test -e .env || cp .env.example .env
export PYTHONHASHSEED=42
.venv/bin/python -m scripts.verify_corpus
.venv/bin/python -m scripts.prepare_model
.venv/bin/python -m scripts.build_index
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.serve
```

For a runtime-only environment, install `requirements.txt` instead. `waitress` supplies the local WSGI server on Windows and Unix systems. The Flask debug server is not needed for the documented run command. The default bind address is loopback; no public service is created by setup.

## Configuration and secrets

### Windows test temporary-directory permissions

If pytest reports `PermissionError: [WinError 5]` for `AppData/Local/Temp/pytest-of-...`, its default temporary directory is inaccessible to the current process. The project config now uses `.pytest_cache/tmp` instead, so the normal test command works without administrator privileges or changing Windows folder permissions.

For an older extracted copy, use this command from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache/tmp
```

For the permanent fix, set `addopts = "-ra --basetemp=.pytest_cache/tmp"` in `pyproject.toml`. This dedicated directory is disposable: pytest clears it before each run. It is already excluded from Git; do not store project files there. Run one test invocation at a time with this directory, or choose a separate dedicated `--basetemp` for concurrent runs.

### Application settings

| Setting | Default | Purpose |
|---|---|---|
| `APP_HOST` | `127.0.0.1` | Waitress bind address |
| `APP_PORT` | `8000` | Validated TCP port, 1-65535 |
| `RANDOM_SEED` | `42` | Seeds Python's standard random generator |
| `PYTHONHASHSEED` | Set in shell to `42` | Fixes Python hash randomization before startup |

The process environment overrides `.env`. Only the `.env` in this repository is read. Invalid integer settings fail startup with a clear configuration error. Local indexing requires no API key. Stage 4 chat reads GROQ_API_KEY and LLM_MODEL from .env. Real keys belong in ignored `.env` files or a hosting provider's secret settings, never in the source, example configuration, tests, or evaluation logs.

`PYTHONHASHSEED` cannot be made effective by changing a `.env` after Python has started. Future numerical libraries will need their own seeds. Fixed seeds do not make a remote LLM deterministic; record provider, model, prompt, temperature, retrieval settings, and source hashes during later evaluation.

## Repository layout

```text
app.py                         WSGI entry point
policy_assistant/              App, settings, parsers, chunking, embeddings, index
policy_assistant/templates/    Foundation landing page
scripts/                       Bootstrap, serving, and verification commands
tests/                         Foundation, parsing, chunking, storage checks
corpus/                        12 canonical Markdown documents; index only these
corpus-manifest.json            Stage 1 IDs, source hashes, and PDF page mapping
bank-policy-review.pdf         Human review copy; never index alongside Markdown
CORPUS-PERMISSION.txt           Synthetic corpus provenance and reuse notice
evaluation/                    Gold questions and scoring plan; never index
evaluation/runs/               Ignored evaluation-run output directory
data/index/                    Ignored persistent vector database directory
data/cache/                    Ignored local cache directory
docs/                          Stage records and requirement checklist
requirements.in                Direct runtime dependency choices
requirements.txt               Exact runtime versions with artifact hashes
requirements-dev.in            Direct development/tooling dependency choices
requirements-dev.txt           Full development lock, including runtime packages
design-and-evaluation.md        Design decisions and honest evaluation status
ai-tooling.md                   AI-assistance disclosure
```

## Reproducibility and integrity

`python -m scripts.verify_corpus` checks the explicit canonical allowlist, document count, duplicate IDs, and SHA-256 content hashes. It fails on changed, missing, or extra supported source files and rejects paths outside the allowed corpus. It does not create embeddings or claim the policy text is legally correct. Health returns HTTP 503 if this verification fails and does not expose filesystem paths.

When editing policies, deliberately update the manifest, review edition, affected gold answers, and corpus version together. Do not automatically replace the expected hashes just to make a failing check pass. Preserve the scored set separately from development examples. The Stage 1 manifest's `indexed: true` means designated for future ingestion, not evidence that an index has already been built.

Ordinary setup uses the checked-in locks and **does not resolve new versions**. To intentionally change dependencies, edit the `.in` file, use the pinned development tools, regenerate both locks, inspect the diff, and verify a clean installation:

```powershell
$env:PIP_CACHE_DIR = Join-Path (Get-Location) 'data/cache/pip'
.\.venv\Scripts\python.exe -m piptools compile --cache-dir data/cache/pip-tools --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file requirements.txt requirements.in
.\.venv\Scripts\python.exe -m piptools compile --cache-dir data/cache/pip-tools --generate-hashes --allow-unsafe --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file requirements-dev.txt requirements-dev.in
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

Hashes verify downloaded package artifacts; they are not a promise of byte-identical runtime behavior on every platform. The Python interpreter and OS remain part of the recorded environment. See [Stage 2 verification](docs/stage-2-verification.md) for the actual checks performed.

## Project stages and current limits

1. **Complete, draft corpus:** fictional profile, eleven policies, source manifest, 25 scored evaluation questions, and five separate development prompts.
2. **Complete, foundation:** virtual environment, dependency locks, configuration, corpus checks, local application startup, and documentation.
3. **Implemented:** Markdown/HTML/PDF/TXT parsing, deterministic chunking, local MiniLM embeddings, Chroma indexing, and terminal top-k search.
4. **Complete, development checks verified:** hybrid retrieval, Groq generation adapter, citation validation, web chat, `/chat`, and source viewer.
5. **In progress:** held-out HTTP evaluation, evidence capture, human review, and quality/latency reports. See [Stage 5 instructions](docs/stage-5-guide.md).
6. **Later:** GitHub Actions on push/PR, optional hosting, final design documentation, demo, and submission PDF.

The local Git repository does not by itself create a GitHub repository, publish files, grant grader access, run CI, or deploy the application. Those actions remain in later stages. No real banking data, paid content, private organizational policies, or operational credentials are included.
