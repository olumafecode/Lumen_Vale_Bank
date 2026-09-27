import hashlib
import json
from pathlib import Path
import re

import pytest

from policy_assistant.chunking import make_chunks
from policy_assistant.config import PROJECT_ROOT
from policy_assistant.corpus import verify_corpus
from policy_assistant.documents import Section, parse_document, parse_markdown
from policy_assistant.indexing import Retriever, build_index, index_status


class WordTokenizer:
    """Deterministic test double; production uses MiniLM's actual WordPiece tokenizer."""
    def offsets(self, text):
        return [match.span() for match in re.finditer(r"\S+", text)]

    def count(self, text):
        return len(self.offsets(text)) + 2


ENTRY = {"document_id": "TEST-01", "title": "Example policy", "path": "corpus/example.md",
         "sha256": "a" * 64, "version": "1.0"}


def test_real_corpus_sections_match_manifest_without_front_matter():
    manifest = json.loads((PROJECT_ROOT / "corpus-manifest.json").read_text(encoding="utf-8"))
    total = 0
    for entry in manifest["documents"]:
        sections = parse_document(PROJECT_ROOT / entry["path"])
        assert {entry["document_id"] + "#" + s.label for s in sections} == set(entry["section_ids"])
        assert all("Document ID:" not in s.text and "PRINT PAGE BREAK" not in s.text for s in sections)
        total += len(sections)
    assert total == 104


def test_numbered_sections_keep_body_and_reject_duplicate_ids():
    sections = parse_markdown("## 1. Policy\n### 1.1 Rules\nFirst rule.\n### 1.2 Other\nSecond rule.")
    assert [s.label for s in sections] == ["1.1", "1.2"]
    assert sections[0].text == "First rule."
    with pytest.raises(ValueError, match="Duplicate"):
        parse_markdown("## 1. Same\nOne.\n## 1. Same\nTwo.")


def test_utf8_text_cleanup_and_unsupported_format(tmp_path):
    file = tmp_path / "policy.txt"
    file.write_text("\ufeffA   rule.\r\n\r\n\r\nAnother\t rule.\x00", encoding="utf-8")
    assert parse_document(file)[0].text == "A rule.\n\nAnother rule."
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document(tmp_path / "ignored.csv")


def test_empty_document_is_explicit_error(tmp_path):
    file = tmp_path / "empty.txt"
    file.write_text(" \n ")
    with pytest.raises(ValueError, match="empty"):
        parse_document(file)


def test_html_strips_noncontent_and_preserves_heading(tmp_path):
    pytest.importorskip("bs4")
    file = tmp_path / "policy.html"
    file.write_text("<html><head><title>Title</title><script>secretScript</script></head>"
                    "<body><nav>menu</nav><h2>2.1 Leave</h2><p>Request <b>approval</b>.</p>"
                    "<p hidden>hiddenText</p><footer>footerText</footer></body></html>", encoding="utf-8")
    sections = parse_document(file)
    assert sections[0].label == "2.1"
    assert "approval" in sections[0].text
    assert all(s.page == 0 and s.line_start == 0 for s in sections)
    assert not any(word in " ".join(s.text for s in sections)
                   for word in ("secretScript", "hiddenText", "footerText", "menu"))


def write_test_pdf(path):
    """Small real text PDF fixture; no rendering dependency is needed."""
    stream = b"BT /F1 12 Tf 72 700 Td (Policy: keep customer records private.) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    path.write_bytes(data)


def test_pdf_extracts_actual_text_and_keeps_page(tmp_path):
    pytest.importorskip("pypdf")
    path = tmp_path / "policy.pdf"
    write_test_pdf(path)
    sections = parse_document(path)
    assert sections[0].page == 1
    assert sections[0].label == "page-1"
    assert "keep customer records private" in sections[0].text


def test_image_only_or_blank_pdf_requires_review(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    path = tmp_path / "blank.pdf"
    writer.write(path)
    with pytest.raises(ValueError, match="OCR or blank-page review"):
        parse_document(path)


def test_chunk_windows_cover_all_words_overlap_and_have_stable_ids():
    body = " ".join(f"word{i}" for i in range(120))
    sections = [Section("1.1", "Rules", body)]
    chunks = make_chunks(ENTRY, sections, WordTokenizer(), max_tokens=40, overlap_tokens=6)
    assert len(chunks) > 1
    assert chunks == make_chunks(ENTRY, sections, WordTokenizer(), 40, 6)
    assert all(c.metadata["token_count"] <= 40 for c in chunks)
    assert set(body.split()) == set(" ".join(c.text for c in chunks).split())
    for left, right in zip(chunks, chunks[1:]):
        assert left.metadata["char_end"] > right.metadata["char_start"]
    assert all(c.metadata["section_id"] == "TEST-01#1.1" for c in chunks)
    assert all(c.text == body[c.metadata["char_start"]:c.metadata["char_end"]] for c in chunks)


def test_changed_source_hash_changes_chunk_ids():
    sections = [Section("1.1", "Rules", "Some policy words here.")]
    before = make_chunks(ENTRY, sections, WordTokenizer())
    after = make_chunks(ENTRY | {"sha256": "b" * 64}, sections, WordTokenizer())
    assert before[0].id != after[0].id


@pytest.mark.parametrize("maximum,overlap", [(0, 0), (300, 30), (40, 21), (40, -1)])
def test_invalid_windows_are_rejected(maximum, overlap):
    with pytest.raises(ValueError):
        make_chunks(ENTRY, [Section("1", "Rule", "Text")], WordTokenizer(), maximum, overlap)


def test_missing_and_invalid_index_status(tmp_path):
    assert index_status(tmp_path) == {"status": "missing", "ready": False}
    folder = tmp_path / "data/index"
    folder.mkdir(parents=True)
    (folder / "active.json").write_text("not JSON")
    assert index_status(tmp_path) == {"status": "invalid", "ready": False}


class FakeEmbedding(WordTokenizer):
    """Storage tests only: this is never selected by any application command."""
    def __init__(self):
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        return [[1.0] + [0.0] * 383 for _ in texts]


@pytest.fixture
def small_corpus(tmp_path):
    folder = tmp_path / "corpus"
    folder.mkdir()
    entries = []
    for i in range(5):
        file = folder / f"policy-{i}.txt"
        file.write_text(f"Policy {i}: protect customer records and report incidents promptly.")
        entries.append({"document_id": f"T-{i}", "title": f"Policy {i}",
                        "path": f"corpus/{file.name}", "version": "1.0", "indexed": True,
                        "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
    (tmp_path / "corpus-manifest.json").write_text(json.dumps(
        {"corpus_id": "test-only", "canonical_document_count": 5, "documents": entries}))
    return tmp_path


def test_text_format_allowlist_and_unlisted_file_detection(small_corpus):
    assert verify_corpus(small_corpus)["source_format"] == "mixed"
    (small_corpus / "corpus/unlisted.html").write_text("<p>Do not ingest me</p>")
    with pytest.raises(ValueError, match="Unlisted"):
        verify_corpus(small_corpus)


def test_persistent_index_reuse_and_stale_source_rejection(small_corpus):
    pytest.importorskip("chromadb")
    pytest.importorskip("pypdf")
    pytest.importorskip("bs4")
    fake = FakeEmbedding()
    report = build_index(small_corpus, embedder=fake)
    assert report["chunks"] == 5 and fake.calls == 1
    second = build_index(small_corpus, embedder=fake)
    assert second["fingerprint"] == report["fingerprint"]
    assert second["reused_collection"] is True and fake.calls == 1
    retriever = Retriever(small_corpus, embedder=fake)
    assert len(retriever.search("customer records", k=3)) == 3
    (small_corpus / "corpus/policy-0.txt").write_text("Changed after indexing.")
    assert index_status(small_corpus)["status"] == "stale"
    with pytest.raises(ValueError, match="changed"):
        retriever.search("customer records")


def test_failed_embedding_does_not_publish_active_index(small_corpus):
    pytest.importorskip("chromadb")
    pytest.importorskip("pypdf")
    pytest.importorskip("bs4")

    class Broken(FakeEmbedding):
        def embed(self, texts):
            raise RuntimeError("Simulated embedding failure")

    with pytest.raises(RuntimeError, match="Simulated"):
        build_index(small_corpus, embedder=Broken())
    assert not (small_corpus / "data/index/active.json").exists()
    assert not (small_corpus / "data/index/.build.lock").exists()


def test_model_download_hash_failure_does_not_publish_cache(tmp_path, monkeypatch):
    import io
    from policy_assistant import embedding
    monkeypatch.setattr(embedding.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"invalid archive"))
    with pytest.raises(ValueError, match="pinned SHA-256"):
        embedding.prepare_model(tmp_path)
    assert not (tmp_path / "data/cache/minilm/model-integrity.json").exists()


def test_existing_model_cache_detects_changed_component(tmp_path):
    from policy_assistant.embedding import MODEL_FILES, MODEL_SHA256, verify_model
    cache = tmp_path / "data/cache/minilm"
    folder = cache / "onnx"
    folder.mkdir(parents=True)
    hashes = {}
    for name in MODEL_FILES:
        (folder / name).write_bytes(b"fixture")
        hashes[name] = hashlib.sha256(b"fixture").hexdigest()
    (cache / "model-integrity.json").write_text(json.dumps(
        {"archive_sha256": MODEL_SHA256, "files": hashes}))
    assert verify_model(tmp_path)["archive_sha256"] == MODEL_SHA256
    (folder / "model.onnx").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_model(tmp_path)


def test_failed_new_build_preserves_previous_active_index(small_corpus):
    pytest.importorskip("chromadb")
    pytest.importorskip("pypdf")
    pytest.importorskip("bs4")
    initial = build_index(small_corpus, embedder=FakeEmbedding())
    previous = (small_corpus / "data/index/active.json").read_bytes()

    class Broken(FakeEmbedding):
        def embed(self, texts):
            raise RuntimeError("Simulated rebuild failure")

    with pytest.raises(RuntimeError, match="Simulated"):
        build_index(small_corpus, max_tokens=180, embedder=Broken())
    assert (small_corpus / "data/index/active.json").read_bytes() == previous
    assert index_status(small_corpus)["fingerprint"] == initial["fingerprint"]
