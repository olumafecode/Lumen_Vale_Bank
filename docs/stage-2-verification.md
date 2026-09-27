# Stage 2 verification record

Verified on 26 September 2026 using Python 3.12.14 on Windows. Stage 2 is the reproducible foundation, not the completed RAG application.

## Results

| Check | Observed result |
|---|---|
| Isolated local virtual environment | Created successfully with Python 3.12.14 |
| Runtime lock | 9 packages pinned with SHA-256 artifact hashes |
| Development/tooling lock | 21 packages pinned with SHA-256 artifact hashes, including runtime packages |
| Exported source checkout and separate environment | Installed from checked-in locks using `--require-hashes` |
| Runtime-only installation | Successful before adding development tools |
| Runtime and development `pip check` | No broken requirements found |
| `python -c "import app"` | Successful with runtime-only dependencies |
| Canonical corpus verification | All 12 source hashes match Stage 1 |
| Original evaluation material | All five Stage 1 evaluation files preserved byte-for-byte |
| Focused foundation tests | 14 passed locally and in exported checkout |
| Real Waitress HTTP startup | GET `/` returned 200; GET `/health` returned 200 |
| RAG readiness | Explicitly false; no model or index exists yet |
| Python bootstrap helper | Successful on exported checkout; created `.env` and ran verification |
| Local server lifecycle | Verification server terminated after checks |
| Git | Local `main` initialized; no remote, publication, or commit |
| Ignore rules | `.env`, virtual environments, caches, and model-run output excluded |

The HTTP check used an available loopback port to avoid disturbing another local service. The documented default remains 127.0.0.1:8000. The normal run command uses Waitress and does not enable Flask debug mode. No persistent demo server is left running by these checks.

## What the tests exercise

The test suite checks honest RAG readiness, successful source verification, landing-page status, altered/missing/extra policy files, unsafe or evaluation-file manifest paths, duplicate document IDs, invalid port configuration, and process-environment precedence over `.env`. It does not claim to test retrieval, generation, citations, model quality, or hosting.

The clean-checkout exercise created a separate environment and installed only runtime dependencies first, then imported the app and made actual HTTP requests. It subsequently ran the documented Python bootstrap to install the full development lock and execute the tests. A preliminary PowerShell helper was blocked by the host's execution policy; it was replaced with Python rather than changing that policy. A preliminary check started before one package installation had finished; final checks were rerun after installation completed and passed.

## Boundaries

No API key, LLM request, model download, vector index, GitHub Actions run, remote repository, or public deployment was used. Groundedness, citation accuracy, and model latency remain NOT_RUN. The source corpus remains synthetic draft content. Linux and macOS commands are documented but have not been executed on those operating systems.

See `stage-2-verification.json` for machine-readable versions and results. The ZIP excludes `.venv`, `.env`, `.git`, caches, and generated evaluation runs; recreate the environment using the root README. Source dependencies and documentation are included.
