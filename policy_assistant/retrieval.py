"""Hybrid retrieval: local dense search plus BM25, fused without gold-answer input."""
from collections import Counter
import math
import re

from .corpus import verify_corpus
from .indexing import Retriever, index_status

STOPWORDS = set("a an the is are was were do does can may must should to of for in on and or with what who how when much be it its our".split())


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


class HybridRetriever(Retriever):
    def __init__(self, root, embedder=None):
        super().__init__(root, embedder)
        rows = self.collection.get(include=["documents", "metadatas"])
        self.rows = [{"chunk_id": i, "text": t, "metadata": m}
                     for i, t, m in zip(rows["ids"], rows["documents"], rows["metadatas"])]
        self.counts = [Counter(words(h["metadata"]["title"] + " " +
                                    h["metadata"]["section_title"] + " " + h["text"])) for h in self.rows]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / len(self.lengths)
        self.df = Counter(w for c in self.counts for w in c)

    def check_fresh(self):
        verify_corpus(self.root)
        status = index_status(self.root)
        if not status["ready"] or status["fingerprint"] != self.record["fingerprint"]:
            raise ValueError("The index changed. Restart the server after rebuilding.")

    def search(self, question, k=4):
        if not isinstance(question, str) or not question.strip() or not 1 <= k <= 20:
            raise ValueError("Provide a question and k between 1 and 20.")
        # Split only explicit question boundaries, never fabricate missing facts.
        parts = [p.strip(" ,") for p in re.split(
            r"\?\s*(?:also,?\s*)?|\s+and\s+(?=(?:does|can|must|should|what|when|who|how)\b)",
            question, flags=re.I) if p.strip(" ,")]
        if not 2 <= len(parts) <= 3:
            return self._search_one(question, k)
        rankings = [self._search_one(part, k) for part in parts]
        merged, seen = [], set()
        for rank in range(k):
            for ranking in rankings:
                if rank < len(ranking):
                    hit = ranking[rank]
                    if hit["chunk_id"] not in seen:
                        merged.append(hit)
                        seen.add(hit["chunk_id"])
        return merged[:min(12, k * len(parts))]

    def _search_one(self, question, k=4):
        if not isinstance(question, str) or not question.strip() or not 1 <= k <= 20:
            raise ValueError("Provide a question and k between 1 and 20.")
        self.check_fresh()
        dense = super().search(question, k=20)
        terms = set(words(question))
        scored = []
        for row, counts, length in zip(self.rows, self.counts, self.lengths):
            score = 0
            for term in terms:
                tf = counts[term]
                if tf:
                    idf = math.log(1 + (len(self.rows) - self.df[term] + .5) / (self.df[term] + .5))
                    score += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * length / self.average))
            if score:
                scored.append((score, row))
        lexical = [r for _, r in sorted(scored, key=lambda pair: (-pair[0], pair[1]["chunk_id"]))[:20]]
        by_id = {h["chunk_id"]: dict(h) for h in dense}
        fused = Counter()
        for ranking in (dense, lexical):
            for rank, hit in enumerate(ranking, 1):
                by_id.setdefault(hit["chunk_id"], dict(hit))
                fused[hit["chunk_id"]] += 1 / (60 + rank)
        return [dict(by_id[i], retrieval_score=fused[i])
                for i in sorted(fused, key=lambda i: (-fused[i], i))[:k]]

    def source(self, chunk_id):
        self.check_fresh()
        return next((h for h in self.rows if h["chunk_id"] == chunk_id), None)
