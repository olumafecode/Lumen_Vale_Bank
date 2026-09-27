"""Verify the Stage 1 allowlist and hashes without parsing, embedding, or indexing."""

import hashlib
import json
from pathlib import Path, PurePosixPath


SUPPORTED_SUFFIXES = {".md", ".txt", ".html", ".htm", ".pdf"}


class CorpusError(ValueError):
    """The canonical corpus is missing, changed, or inconsistent with its manifest."""


def verify_corpus(root: Path) -> dict:
    root = root.resolve()
    corpus_dir = (root / "corpus").resolve()
    try:
        if not corpus_dir.is_relative_to(root):
            raise CorpusError("Corpus directory must remain inside the project")
        manifest = json.loads((root / "corpus-manifest.json").read_text(encoding="utf-8"))
        documents = manifest["documents"]
        if not isinstance(documents, list) or not 5 <= len(documents) <= 20:
            raise CorpusError("Corpus must contain 5-20 manifest documents")
        if manifest["canonical_document_count"] != len(documents):
            raise CorpusError("Manifest document count does not match")
        seen_ids, seen_paths = set(), set()
        for entry in documents:
            doc_id, relative = entry["document_id"], PurePosixPath(entry["path"])
            # Do not accept an arbitrary directory walk or index the gold answers.
            if (relative.is_absolute() or len(relative.parts) != 2
                    or relative.parts[0] != "corpus" or relative.suffix.lower() not in SUPPORTED_SUFFIXES
                    or "\\" in entry["path"]):
                raise CorpusError("Manifest path is outside the canonical policy-file allowlist")
            path = (root / relative).resolve()
            if path.parent != corpus_dir:
                raise CorpusError("Manifest file resolves outside the corpus directory")
            if doc_id in seen_ids or path in seen_paths:
                raise CorpusError("Duplicate document ID or path in manifest")
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise CorpusError(f"Content hash mismatch for {doc_id}")
            seen_ids.add(doc_id)
            seen_paths.add(path)
        actual_paths = {p.resolve() for p in corpus_dir.iterdir()
                        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES}
        if actual_paths != seen_paths:
            raise CorpusError("Unlisted or missing policy documents in corpus")
        return {"status": "verified", "corpus_id": manifest["corpus_id"],
                "documents": len(documents), "source_format": ("markdown" if all(p.suffix.lower() == ".md" for p in seen_paths) else "mixed")}
    except CorpusError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CorpusError("Corpus files or manifest are missing or invalid") from exc
