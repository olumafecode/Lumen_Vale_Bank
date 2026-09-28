# Requirement-to-evidence checklist

| Assignment item | Evidence | Status after Stage 4 implementation |
|---|---|---|
| Legal-to-use company-policy corpus, 5-20 files / 30-120 pages | 12 Markdown sources, 35-page review PDF, manifest, reuse notice | Draft complete |
| Define information-quality and system metrics | Evaluation scoring plan | Targets defined, not measured |
| Virtual environment | Local `.venv`, reproducible setup commands | Complete locally; excluded from Git/ZIP |
| Dependencies | Hashed `requirements.txt`, `requirements-dev.txt`, direct `.in` files | Complete for implemented ingestion and retrieval |
| Setup/run instructions | Root README and Python helper | Complete |
| Seeds where applicable | Settings and documented pre-launch hash seed | Foundation complete; extend with numerical libraries later |
| PDF/HTML/Markdown/TXT parsing and cleaning | documents.py and parser tests | Complete for text-based inputs; no OCR |
| Chunking, embedding, vector storage | 106 chunks, local MiniLM, persistent Chroma; Stage 3 verification | Complete |
| Top-k retrieval and cited LLM generation | Hybrid retrieval and Groq adapter | Implemented; five live development answers verified |
| Scope refusal, answer limits, source validation | Prompt, output validator, test suite | Implemented; two live refusal probes passed; formal evaluation pending |
| Web chat `/` and POST `/chat` | Routes, interface, source links and snippets | Implemented; missing-key browser path verified |
| JSON `/health` | Flask route with source verification and explicit RAG readiness | Corpus and index status implemented |
| Public deployment or working local demo | Later stages | Local chat and live API smoke checks verified; recorded demo pending |
| GitHub Actions on push/PR | .github/workflows/ci.yml | Implemented; first hosted run must be verified after push |
| 15-30 evaluation questions | 25 scored cases, separate five development prompts | Draft complete |
| Groundedness and citation accuracy results | Later model evaluation | NOT_RUN |
| p50/p95 end-to-end latency for 10-20 queries | Planned 20-query run | NOT_RUN |
| Design and evaluation document | Root `design-and-evaluation.md` | Current-stage decisions and planned choices recorded |
| AI tooling disclosure | Root `ai-tooling.md` | Current-stage disclosure complete |
| GitHub repository and `quantic-grader` access | Later publishing step | Local Git only |
| 5-10 minute recorded demo | Later presentation step | Not recorded |
| Single submission PDF with repository and video links | Final packaging | Not created |

This checklist follows the supplied assignment. Public deployment is optional; a local RAG demonstration is acceptable. A local foundation health check does not satisfy the final working-RAG demonstration requirement.
