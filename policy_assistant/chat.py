"""Grounded-answer contract and validated source attribution."""
import re

REFUSAL = "I can only answer about our policies. I could not find enough supporting evidence to answer this question."
PROMPT_VERSION = "policy-claims-v2-schema"


class AnswerValidationError(ValueError):
    pass


def normalized(text):
    return " ".join(text.split())


def validate_answer(result, hits):
    if not isinstance(result, dict) or type(result.get("answerable")) is not bool:
        raise AnswerValidationError("Invalid answer structure")
    if result["answerable"] is False:
        return {"answer": REFUSAL, "claims": [], "citations": [], "refused": True}
    claims = result.get("claims")
    if not isinstance(claims, list) or not 1 <= len(claims) <= 5:
        raise AnswerValidationError("Missing supported claims")
    allowed = {h["chunk_id"]: h for h in hits}
    citations, output, seen, total = [], [], {}, 0
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str):
            raise AnswerValidationError("Invalid claim")
        text = claim["text"].strip()
        total += len(text.split())
        if not text or len(text) > 1600 or total > 180 or re.search(r"https?://|\[\d+\]", text):
            raise AnswerValidationError("Invalid claim length or markup")
        refs = claim.get("citations")
        if not isinstance(refs, list) or not 1 <= len(refs) <= 3:
            raise AnswerValidationError("Every claim requires evidence")
        numbers = []
        for ref in refs:
            if not isinstance(ref, dict):
                raise AnswerValidationError("Invalid citation")
            cid, quote = ref.get("chunk_id"), ref.get("quote")
            if not isinstance(cid, str) or cid not in allowed or not isinstance(quote, str):
                raise AnswerValidationError("Citation is outside retrieved evidence")
            quote = normalized(quote)
            hit = allowed[cid]
            if not 20 <= len(quote) <= 1800 or quote not in normalized(hit["text"]):
                raise AnswerValidationError("Quote is not an exact source passage")
            identity = (cid, quote)
            if identity not in seen:
                number = len(citations) + 1
                seen[identity] = number
                citations.append({"number": number, "chunk_id": cid,
                                  "document_id": hit["metadata"]["document_id"],
                                  "title": hit["metadata"]["title"],
                                  "section_id": hit["metadata"]["section_id"],
                                  "snippet": quote, "url": "/sources/" + cid})
            numbers.append(seen[identity])
        output.append({"text": text, "citation_numbers": sorted(set(numbers))})
    answer = "\n\n".join(c["text"] + " " + " ".join(f"[{n}]" for n in c["citation_numbers"])
                        for c in output)
    return {"answer": answer, "claims": output, "citations": citations, "refused": False}
