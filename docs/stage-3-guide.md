# Stage 3: document ingestion and searchable policy index

Status: complete and verified locally. The 12 documents produce 106 chunks; all 34 tests pass. See [recorded results and limitations](stage-3-status.md).

## Commands in the VS Code terminal

Run these from the project root using the Python 3.12 virtual environment.

1. One-time transition from Stage 2 (requires internet):
   .\.venv\Scripts\python.exe -m scripts.prepare_stage3

   This resolves and writes hashed runtime/development locks, installs them, checks dependency compatibility, and downloads the pinned public MiniLM archive. It does not need an API key and does not build the index.

2. Build the index:
   .\.venv\Scripts\python.exe -m scripts.build_index

3. Inspect real retrieved passages:
   .\.venv\Scripts\python.exe -m scripts.search "How many annual leave days do full-time staff receive?"

4. Run the five development retrieval questions:
   .\.venv\Scripts\python.exe -m scripts.evaluate_retrieval

5. Run tests:
   .\.venv\Scripts\python.exe -m pytest -q

6. Start the web foundation:
   .\.venv\Scripts\python.exe -m scripts.serve

After locks have been finalized, fresh installations should use the checked-in requirements-dev.txt with --require-hashes, followed by scripts.prepare_model and scripts.build_index. They need not resolve dependencies again. The setup command is for the intentional Stage 2-to-3 dependency change. Do not change locks while another setup or test run is using them.

## What ingestion does

The manifest is the only source allowlist. The twelve original Markdown policies remain canonical; the review PDF and all evaluation files are excluded. Markdown, UTF-8 TXT, HTML, and text-based PDF are supported by the parser and manifest validator for future explicitly listed corpus documents. Adding a new format requires updating the manifest and hash intentionally; it does not authorize a recursive scan.

Markdown front matter belonging to this synthetic corpus and print comments are removed. Numbered section identifiers are preserved. HTML scripting/navigation/style content is removed and heading-based citations retained. PDF records retain page numbers; repeated edge headers/footers are removed. A PDF page with no extractable text produces an explicit error requiring OCR or blank-page review. OCR and complex visual table interpretation are not implemented.

Sections are split into deterministic token windows using MiniLM's actual tokenizer. Each embedding input includes the document title and section heading. The default total maximum is 220 tokens (including special tokens), with approximately 30 tokens of overlap within a section. The 256-token model limit is checked before embedding; no silent truncation is accepted. Chunks never combine different sections.

Every chunk retains its document ID, title, source path/hash, section ID/heading, source page or Markdown line range, version, effective date, and character offsets within the normalized section text. Character offsets are not raw file-byte offsets. A stable SHA-256 chunk ID incorporates content, source identity, and chunk settings.

## Embedding and storage design

The model is all-MiniLM-L6-v2, executed locally on CPU using Chroma's ONNX embedding implementation. This implements the previously proposed model without requiring PyTorch or a paid embedding endpoint. Vectors have 384 dimensions; the index uses cosine distance.

The public model archive is pinned by SHA-256:
913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3

The download is saved in data/cache/minilm, validated before extraction, and restricted to the expected regular model files. A component-hash record is checked before inference. The code never loads a hosted LLM, reads provider keys, or downloads a model implicitly during a search. Once dependencies and the model are cached, build/search run locally.

Chroma persists under data/index/chroma. Each configuration/source snapshot gets a separate collection based on its fingerprint. A completed build verifies all intended IDs and publishes data/index/active.json atomically. An interrupted build leaves the previous active index intact. Repeating an unchanged build reuses the existing collection without adding duplicate chunks. Prior collections are retained; no automatic destructive cleanup is performed.

A build lock prevents concurrent writers. If a process was forcibly terminated, confirm no build is running before removing only data/index/.build.lock. Do not delete the entire project or corpus to resolve an indexing issue.

## Search and readiness

scripts.search returns passages, source metadata, stable chunk IDs, and cosine distances. A lower distance means a closer vector match; it is not an answer confidence score or a probability. This command is an inspection tool, not the final chatbot.

The health endpoint reports corpus integrity and index state. rag_ready stays false because generation, chat, and citation-linked UI remain Stage 4 work. Index status checks source freshness and artifact presence; opening the retriever additionally checks the Chroma collection and verifies the model cache.

Changed or missing policy files cause integrity verification to fail. A deliberate policy update requires coordinated manifest changes and an index rebuild. Changing chunk configuration produces a new versioned collection.

## Validation and evaluation boundaries

Tests cover real source section IDs, Markdown/TXT/HTML/PDF parsing, empty/scanned-PDF errors, token-window coverage, overlap, stable IDs, stale indexes, persistence, reuse, and incomplete-build handling. Storage tests use an explicit test double for embeddings; production commands always use MiniLM.

Full verification also built and reopened the real model/index, confirmed reuse, and ran the development retrieval prompts. The five development questions are the only question file used by scripts.evaluate_retrieval. The 25 held-out answer-quality questions and reference answers are not ingested or used to tune retrieval in this stage. Development hit rate is not groundedness, citation accuracy, or final request-to-answer latency.

## Primary technical references

- Chroma's pinned ONNX implementation: https://github.com/chroma-core/chroma/blob/1.5.9/chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py
- Chroma storage of provided embeddings and source metadata: https://docs.trychroma.com/docs/collections/add-data
- Original embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
