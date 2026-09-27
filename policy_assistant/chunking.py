"""Deterministic token windows within individual source sections."""
from dataclasses import dataclass
import hashlib
import json

from .documents import Section


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    embedding_text: str
    metadata: dict


def make_chunks(entry: dict, sections: list[Section], tokenizer,
                max_tokens: int = 220, overlap_tokens: int = 30) -> list[Chunk]:
    if not 32 <= max_tokens <= 256 or not 0 <= overlap_tokens < max_tokens // 2:
        raise ValueError("Use 32-256 total tokens and overlap less than half the window.")
    chunks = []
    for section in sections:
        prefix = f"{entry['title']}\n{section.heading}\n"
        budget = max_tokens - tokenizer.count(prefix) - 2
        if budget <= overlap_tokens:
            raise ValueError("Heading leaves insufficient room for text and overlap.")
        offsets = tokenizer.offsets(section.text)
        start = 0
        while start < len(offsets):
            end = min(start + budget, len(offsets))
            while end > start:
                left, right = offsets[start][0], offsets[end - 1][1]
                text = section.text[left:right]
                embedding_text = prefix + text
                if tokenizer.count(embedding_text) <= max_tokens:
                    break
                end -= 1
            if end <= start:
                raise ValueError("Unable to produce a chunk within the token budget.")
            identity = {"doc": entry["document_id"], "source_sha256": entry["sha256"],
                        "section": section.label, "page": section.page, "start": left,
                        "end": right, "max_tokens": max_tokens, "overlap": overlap_tokens,
                        "text": embedding_text, "algorithm": "section-window-v1"}
            digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
            metadata = {"document_id": entry["document_id"], "title": entry["title"],
                        "source_path": entry["path"], "source_sha256": entry["sha256"],
                        "section_id": f"{entry['document_id']}#{section.label}",
                        "section_title": section.heading, "page": section.page,
                        "line_start": section.line_start, "line_end": section.line_end,
                        "char_start": left, "char_end": right,
                        "token_count": tokenizer.count(embedding_text),
                        "version": entry.get("version", ""),
                        "effective_date": entry.get("effective_date", "")}
            chunks.append(Chunk(digest, text, embedding_text, metadata))
            if end == len(offsets):
                break
            start = max(start + 1, end - overlap_tokens)
    if not chunks or len({c.id for c in chunks}) != len(chunks):
        raise ValueError("Empty or duplicate chunks.")
    return chunks
