# Stage 1: Lumen Vale Bank synthetic policy corpus

A fictional community-bank profile and eleven policy documents for the Quantic company-policy RAG project. Drafted with AI assistance on 26 September 2026. This is an academic corpus, not operational banking guidance or a claim of legal compliance.

## Contents and scope

The canonical corpus has **12 Markdown files**, **12,002 body words**, and **35 actual pages** in the supplied review PDF. This satisfies the assignment range of 5-20 documents and 30-120 pages. The page count is based on the rendered review edition, not a words-per-page estimate. The company profile occupies two pages; each of the eleven policies occupies three.

| ID | Document | Review PDF pages |
|---|---|---|
| LVB-00 | [Company Profile and Policy Guide](../corpus/lvb-00-company-profile.md) | 1-2 |
| LVB-01 | [Password and Authentication Policy](../corpus/lvb-01-password-and-authentication.md) | 3-5 |
| LVB-02 | [Information Security and Incident Response Policy](../corpus/lvb-02-information-security.md) | 6-8 |
| LVB-03 | [Whistleblowing and Protected Reporting Policy](../corpus/lvb-03-whistleblowing.md) | 9-11 |
| LVB-04 | [Branch Operations and Cash Handling Policy](../corpus/lvb-04-branch-operations.md) | 12-14 |
| LVB-05 | [Staff Leave, Holidays, and Separation Policy](../corpus/lvb-05-leave-holidays-and-separation.md) | 15-17 |
| LVB-06 | [Data Protection, Privacy, and Retention Policy](../corpus/lvb-06-data-protection-and-privacy.md) | 18-20 |
| LVB-07 | [Ethics, Conflicts, and Staff Conduct Policy](../corpus/lvb-07-ethics-and-conduct.md) | 21-23 |
| LVB-08 | [Internal Control, Approvals, and Assurance Policy](../corpus/lvb-08-internal-controls.md) | 24-26 |
| LVB-09 | [Know Your Customer and Know Your Customer's Business Policy](../corpus/lvb-09-kyc-and-kyb.md) | 27-29 |
| LVB-10 | [Internal and Corporate Communication Policy](../corpus/lvb-10-internal-and-corporate-communication.md) | 30-32 |
| LVB-11 | [Remote Work, Travel, and Expense Policy](../corpus/lvb-11-remote-work-travel-and-expenses.md) | 33-35 |

## Indexing contract

Index only `corpus/*.md`, as listed in `corpus-manifest.json`. The review PDF contains the same material for reading and page-count evidence; never index both copies. Do not index this README, the manifest, evaluation files, permission notice, validation report, or ZIP. The corpus currently uses Markdown; parsers for HTML/PDF/TXT and mixed-format fixture checks belong to Stage 3 and have not been implemented.

Each source has a stable document ID, title, owner, version, fictional effective date, and numbered sections. A reference such as `LVB-09#2.1` identifies document LVB-09, section 2.1. These identifiers are citation keys, not promises about a Markdown renderer's automatic anchor syntax. The application should map them to source-viewer anchors. Strip metadata and print-page-break comments from embedding text while retaining metadata on each chunk.

## Important scenario conventions

- LVB is fictional; CU is invented currency, and Lumen time is an invented local convention.
- The policies become effective on 1 October 2026 within the scenario. All are version 1.0 and have a planned review on 1 October 2027.
- StaffHub, AccessDesk, CaseTrack, PolicyHub, internal directories, and `.example` email addresses are fictional and do not function.
- Legal reporting deadlines, real regulators, account interest rates, and parental-leave entitlements are deliberately unspecified. They support abstention tests.
- Security reporting and privacy escalation have different clocks. Business days and calendar days are distinguished. Monetary thresholds explicitly state whether they are inclusive.
- The central retention schedule is LVB-06 section 2.2. Holds override routine deletion. Credentials, medical details, and investigation identities have specific handling restrictions.

## Evaluation package

`evaluation/questions.jsonl` and the readable `questions-and-gold-answers.md` contain 25 scored cases with reference answers and source passages. `development-questions.jsonl` contains five separate development prompts. `success-criteria-and-scoring.md` defines the proposed targets and denominators. `results-template.csv` contains only NOT_RUN placeholders; no performance results have been fabricated.

## Review status and next stage

The corpus was checked for document counts, actual PDF pagination, document/section references, evidence-quote matches, and manifest hashes. Visual QA was performed on the review PDF. The validation report records the checks and their limits. Human editorial acceptance remains pending; the documents are drafts. No RAG pipeline, real API call, GitHub repository, deployment, or final academic submission has been created in Stage 1.

Before freezing version 1.0, the student should read the fictional rules and make any desired changes. Then Stage 2 can establish the application repository and reproducible environment. Stage 3 can implement ingestion and traceable chunking. Preserve evaluation separation and the reuse notice when copying the corpus into the repository.

## Provenance and permissions

See `CORPUS-PERMISSION.txt`. No external policy sources, private data, paid content, or real bank documents were used. AI assistance should be disclosed in the final project's `ai-tooling.md`. The assignment PDF itself is excluded from this package.

