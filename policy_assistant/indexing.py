"""Build versioned Chroma collections; publish only a complete, verified index."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import uuid

from .chunking import make_chunks
from .corpus import verify_corpus
from .documents import parse_document
from .embedding import LocalEmbedding, MODEL_NAME, MODEL_SHA256, file_hash


def _json_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _client(root: Path):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(root / "data/index/chroma"),
                                     settings=Settings(anonymized_telemetry=False))


def index_status(root: Path) -> dict:
    path = root / "data/index/active.json"
    if not path.exists():
        return {"status": "missing", "ready": False}
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        manifest = json.loads((root / "corpus-manifest.json").read_text(encoding="utf-8"))
        expected_sources = {entry["path"]: entry["sha256"] for entry in manifest["documents"]}
        if record["sources"] != expected_sources or record["documents"] != len(expected_sources):
            return {"status": "invalid", "ready": False}
        if record["status"] != "complete" or record["chunks"] < 1:
            return {"status": "invalid", "ready": False}
        if record["manifest_sha256"] != file_hash(root / "corpus-manifest.json"):
            return {"status": "stale", "ready": False}
        if record["model_archive_sha256"] != MODEL_SHA256:
            return {"status": "stale", "ready": False}
        for source, digest in record["sources"].items():
            file = (root / source).resolve()
            if file.parent != (root / "corpus").resolve() or file_hash(file) != digest:
                return {"status": "stale", "ready": False}
        if not (root / "data/index/chroma/chroma.sqlite3").is_file():
            return {"status": "missing", "ready": False}
        return {"status": "built", "ready": True, "chunks": record["chunks"],
                "documents": record["documents"], "fingerprint": record["fingerprint"]}
    except (OSError, KeyError, TypeError, ValueError, AttributeError):
        return {"status": "invalid", "ready": False}


def build_index(root: Path, max_tokens=220, overlap_tokens=30, embedder=None) -> dict:
    verify_corpus(root)
    started = time.perf_counter()
    manifest_sha = file_hash(root / "corpus-manifest.json")
    manifest = json.loads((root / "corpus-manifest.json").read_text(encoding="utf-8"))
    entries = sorted(manifest["documents"], key=lambda d: d["document_id"])
    embedding = embedder or LocalEmbedding(root)
    chunks = []
    for entry in entries:
        sections = parse_document(root / entry["path"])
        chunks.extend(make_chunks(entry, sections, embedding, max_tokens, overlap_tokens))
    versions = {name: importlib.metadata.version(name)
                for name in ("chromadb", "pypdf", "beautifulsoup4", "tokenizers", "onnxruntime")}
    spec = {"algorithm": "section-window-v1", "model_archive_sha256": MODEL_SHA256,
            "max_tokens": max_tokens, "overlap_tokens": overlap_tokens,
            "manifest_sha256": manifest_sha, "packages": versions,
            "chunk_ids": [c.id for c in chunks]}
    fingerprint = _json_hash(spec)
    collection_name = "lvb-" + fingerprint[:32]
    directory = root / "data/index"
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".build.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise ValueError("Index build lock exists. Stop other builds before removing data/index/.build.lock.") from None
    try:
        with handle:
            handle.write(datetime.now(timezone.utc).isoformat())
        client = _client(root)
        collection = client.get_or_create_collection(
            name=collection_name, embedding_function=None,
            configuration={"hnsw": {"space": "cosine", "num_threads": 1}})
        expected_ids = {chunk.id for chunk in chunks}
        stored_ids = set(collection.get(include=[])["ids"])
        reused = stored_ids == expected_ids
        if not reused:
            pending = [c for c in chunks if c.id not in stored_ids]
            for offset in range(0, len(pending), 32):
                batch = pending[offset:offset + 32]
                vectors = embedding.embed([c.embedding_text for c in batch])
                if len(vectors) != len(batch) or any(len(v) != 384 for v in vectors):
                    raise ValueError("Unexpected embedding dimensions.")
                collection.upsert(ids=[c.id for c in batch],
                                  embeddings=vectors, documents=[c.text for c in batch],
                                  metadatas=[c.metadata for c in batch])
            obsolete = sorted(stored_ids - expected_ids)
            if obsolete:
                collection.delete(ids=obsolete)
        if set(collection.get(include=[])["ids"]) != expected_ids:
            raise ValueError("Stored chunk set differs from the intended index.")
        verify_corpus(root)
        if file_hash(root / "corpus-manifest.json") != manifest_sha:
            raise ValueError("Manifest changed during indexing; no new active index was published.")
        record = {"status": "complete", "fingerprint": fingerprint, "collection": collection_name,
                  "model": MODEL_NAME, "model_archive_sha256": MODEL_SHA256,
                  "dimensions": 384, "distance": "cosine", "documents": len(entries),
                  "chunks": len(chunks), "manifest_sha256": manifest_sha,
                  "sources": {d["path"]: d["sha256"] for d in entries},
                  "max_tokens": max_tokens, "overlap_tokens": overlap_tokens,
                  "packages": versions, "reused_collection": reused,
                  "completed_at": datetime.now(timezone.utc).isoformat(),
                  "build_seconds": round(time.perf_counter() - started, 3)}
        (directory / f"chunks-{fingerprint[:16]}.jsonl").write_text(
            "\n".join(json.dumps(asdict(c), ensure_ascii=False) for c in chunks) + "\n",
            encoding="utf-8")
        temporary = directory / f"active-{uuid.uuid4().hex}.tmp"
        temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
        temporary.replace(directory / "active.json")
        return record
    finally:
        lock.unlink(missing_ok=True)


class Retriever:
    def __init__(self, root: Path, embedder=None):
        verify_corpus(root)
        if not index_status(root)["ready"]:
            raise ValueError("Index is missing or stale. Run python -m scripts.build_index.")
        self.root = root
        self.embedding = embedder or LocalEmbedding(root)
        self.record = json.loads((root / "data/index/active.json").read_text(encoding="utf-8"))
        self.client = _client(root)
        self.collection = self.client.get_collection(self.record["collection"], embedding_function=None)
        if self.collection.count() != self.record["chunks"]:
            raise ValueError("Index collection is incomplete; rebuild it.")

    def search(self, question: str, k: int = 4) -> list[dict]:
        if not question.strip() or not 1 <= k <= 20:
            raise ValueError("Provide a nonempty question and k between 1 and 20.")
        if not index_status(self.root)["ready"]:
            raise ValueError("Policy files changed; rebuild the index before searching.")
        results = self.collection.query(
            query_embeddings=self.embedding.embed([question.strip()]),
            n_results=min(k, self.collection.count()),
            include=["documents", "metadatas", "distances"])
        hits = [{"chunk_id": chunk_id, "text": text, "metadata": metadata,
                 "cosine_distance": float(distance)}
                for chunk_id, text, metadata, distance in zip(
                    results["ids"][0], results["documents"][0],
                    results["metadatas"][0], results["distances"][0])]
        return sorted(hits, key=lambda h: (h["cosine_distance"], h["chunk_id"]))
