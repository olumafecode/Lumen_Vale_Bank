# Stage 3 verification

Stage 3 is complete locally: parsing, chunking, local embeddings, persistent Chroma indexing, and terminal retrieval. Verified on Windows with Python 3.12.14 on 2026-09-27 UTC.

## Recorded checks

- Full suite: **34 passed, no skips** (12.06 seconds). Dependency check: no broken requirements.
- All 12 canonical source hashes remain unchanged from Stage 1.
- All 104 numbered subsections are represented in **106 unique chunks**.
- Actual tokenizer maximum: **218 tokens**, below the configured 220 and model limit 256.
- Real CPU MiniLM embeddings have 384 dimensions; sampled vector norm was 1.0.
- Initial index build completed in 11.414 seconds. A second build reused the same collection and fingerprint, with 106 chunks and no duplicates (3.639 seconds).
- Flask health returned HTTP 200, corpus verified, index ready, and rag_ready false as expected before Stage 4.
- Runtime requirements contain 90 pinned packages with artifact hashes. Model archive and component hashes are verified before use.

Fingerprint: 608707a76e72de502d9b83bd8fbf411c250b9bff9380c6293dece6c5f2a9dde9

The test runner used a fresh dedicated directory beneath data/cache and disabled pytest's cache provider because the existing user-created pytest temporary directory was inaccessible to the agent. The ordinary VS Code command retains the project's Windows temp-directory fix.

## Development retrieval baseline

With k=4, **4/5 questions (80%)** retrieved at least one expected section. Mean per-question expected-section recall was **70%**.

| Case | Topic | Expected-section recall |
|---|---|---|
| D01 | Everyday versus privileged administrator accounts | 0% |
| D02 | Independent checking of manual adjustments | 50% |
| D03 | Eligible meal reimbursement | 100% |
| D04 | Whistleblower confidentiality | 100% |
| D05 | Privacy-request response target | 100% |

D01 missed LVB-01#1.2. D02 found LVB-04#2.1 but missed LVB-08#1.2. These are baseline retrieval limitations to address during Stage 4, for example by comparing lexical/semantic retrieval or reranking using development prompts only. No benchmark answers were used to tune this implementation.

Machine-readable evidence: [index integrity](stage-3-integrity.json), [initial build](stage-3-build.json), and [development retrieval with passages](stage-3-development-retrieval.json).

This is not a final RAG evaluation. Groundedness, citation accuracy, refusal behavior, and end-to-end answer latency remain unmeasured. Stage 4 adds the LLM, chat endpoint, citation viewer, and answer guardrails. No public deployment or GitHub CI is claimed.
