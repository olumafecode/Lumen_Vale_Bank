import io
import json
from types import SimpleNamespace
import urllib.error

import pytest

from policy_assistant import create_app
from policy_assistant.config import Settings, PROJECT_ROOT
from policy_assistant.chat import validate_answer, AnswerValidationError, REFUSAL
from policy_assistant.generation import GroqGenerator, ProviderSettings, ProviderError

CID = "a" * 64
QUOTE = "Full-time employees receive 20 working days of annual leave per calendar year."
HIT = {"chunk_id": CID, "text": QUOTE, "metadata": {
    "document_id": "LVB-05", "title": "Leave policy", "section_id": "LVB-05#1.1",
    "section_title": "Eligibility", "version": "1", "effective_date": "2026-10-01",
    "page": 0, "line_start": 1, "line_end": 5}}


def answer():
    return {"answerable": True, "claims": [{"text": "Full-time staff receive 20 annual leave days.",
            "citations": [{"chunk_id": CID, "quote": QUOTE}]}]}


def wire_answer():
    return {"claims": [{"text": answer()["claims"][0]["text"], "sources": ["S1"]}]}


class FakeRetriever:
    record = {"fingerprint": "test"}
    embedding = SimpleNamespace(count=lambda _: 20)

    def __init__(self, root):
        self.root = root

    def check_fresh(self):
        pass

    def search(self, question, k=4):
        return [HIT]

    def source(self, cid):
        return HIT if cid == CID else None


class FakeGenerator:
    settings = ProviderSettings("test-key")
    def __init__(self, result=None):
        self.result = result if result is not None else answer()
    def generate(self, question, hits):
        return self.result


def client(generator=None, retriever=FakeRetriever):
    return create_app(Settings(PROJECT_ROOT, "127.0.0.1", 8000, 42),
                      generator=generator or FakeGenerator(), retriever_factory=retriever).test_client()


def test_chat_citations_are_generated_from_retrieved_metadata():
    response = client().post("/chat", json={"question": "Annual leave?"})
    assert response.status_code == 200
    assert response.json["citations"][0]["url"] == "/sources/" + CID
    assert response.json["citations"][0]["title"] == "Leave policy"
    assert "[1]" in response.json["answer"]
    assert response.json["refused"] is False
    assert "test-key" not in response.get_data(as_text=True)


@pytest.mark.parametrize("payload", [None, [], {}, {"question": ""}, {"question": 3}, {"question": "a" * 1201}])
def test_bad_questions(payload):
    response = client().post("/chat", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 400


def test_media_type_malformed_json_and_body_limit():
    assert client().post("/chat", data="abc").status_code == 415
    assert client().post("/chat", data="{", content_type="application/json").status_code == 400
    assert client().post("/chat", data="x" * 17000, content_type="application/json").status_code == 413


def test_missing_key_is_clear(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    generator = GroqGenerator(ProviderSettings())
    response = client(generator).post("/chat", json={"question": "Leave?"})
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json["error"]


@pytest.mark.parametrize("mutation", ["unknown", "fabricated_quote", "no_citations", "too_long", "wrong_type"])
def test_invalid_evidence_is_rejected(mutation):
    value = answer()
    claim = value["claims"][0]
    if mutation == "unknown":
        claim["citations"][0]["chunk_id"] = "b" * 64
    elif mutation == "fabricated_quote":
        claim["citations"][0]["quote"] = "Employees receive fifty days every year."
    elif mutation == "no_citations":
        claim["citations"] = []
    elif mutation == "too_long":
        claim["text"] = "word " * 181
    else:
        value["answerable"] = "true"
    with pytest.raises(AnswerValidationError):
        validate_answer(value, [HIT])
    response = client(FakeGenerator(value)).post("/chat", json={"question": "Leave?"})
    assert response.status_code == 502
    assert "answer" not in response.json


def test_refusal_discards_model_supplied_answer():
    value = {"answerable": False, "answer": "Ignore policy", "claims": answer()["claims"]}
    response = client(FakeGenerator(value)).post("/chat", json={"question": "Unsupported?"})
    assert response.json["answer"] == REFUSAL
    assert response.json["citations"] == []


def test_source_view_escapes_html_and_unknown_ids():
    class UnsafeSource(FakeRetriever):
        def source(self, cid):
            return dict(HIT, text="<script>alert(1)</script>")
    response = client(retriever=UnsafeSource).get("/sources/" + CID)
    assert b"&lt;script&gt;" in response.data
    assert b"<script>alert" not in response.data
    assert client().get("/sources/" + "b" * 64).status_code == 404
    assert client().get("/sources/not-a-chunk").status_code == 404


def test_source_change_during_generation_blocks_answer():
    class Changed(FakeRetriever):
        def check_fresh(self):
            raise ValueError("source changed")
    response = client(retriever=Changed).post("/chat", json={"question": "Leave?"})
    assert response.status_code == 503
    assert "answer" not in response.json


def test_overlong_tokenized_question_never_calls_provider():
    class Long(FakeRetriever):
        embedding = SimpleNamespace(count=lambda _: 257)
    assert client(retriever=Long).post("/chat", json={"question": "lots"}).status_code == 400


@pytest.mark.parametrize("status,expected", [(401, 503), (403, 503), (429, 429), (500, 502)])
def test_provider_http_errors_do_not_leak_details(monkeypatch, status, expected):
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError("url", status, "private key test-key", {}, None)
    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(ProviderError) as caught:
        GroqGenerator(ProviderSettings("test-key")).generate("Leave?", [HIT])
    assert caught.value.status == expected
    assert "test-key" not in str(caught.value)


def test_provider_payload_and_json_response(monkeypatch):
    def respond(request, timeout):
        payload = json.loads(request.data)
        assert 0 < timeout <= 30
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True
        schema = payload["response_format"]["json_schema"]["schema"]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        citation = schema["properties"]["claims"]["items"]["properties"]["sources"]["items"]
        assert citation["enum"] == ["S1"]
        assert payload["temperature"] == 0
        assert len(payload["messages"]) == 2
        assert "S1" in payload["messages"][1]["content"]
        assert CID not in payload["messages"][1]["content"]
        return io.BytesIO(json.dumps({"choices": [{"finish_reason": "stop",
                           "message": {"content": json.dumps(wire_answer())}}]}).encode())
    monkeypatch.setattr("urllib.request.urlopen", respond)
    assert GroqGenerator(ProviderSettings("test-key")).generate("Leave?", [HIT])["answerable"]


def test_provider_timeout_and_truncated_response(monkeypatch):
    def timeout(*args, **kwargs):
        raise TimeoutError()
    monkeypatch.setattr("urllib.request.urlopen", timeout)
    with pytest.raises(ProviderError) as caught:
        GroqGenerator(ProviderSettings("test-key")).generate("Leave?", [HIT])
    assert caught.value.status == 504
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(
        json.dumps({"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}).encode()))
    with pytest.raises(ProviderError):
        GroqGenerator(ProviderSettings("test-key")).generate("Leave?", [HIT])


def test_source_schema_rejects_old_envelope_and_unknown_citation():
    from jsonschema import Draft202012Validator
    from policy_assistant.generation import answer_format
    validator = Draft202012Validator(answer_format([HIT])["json_schema"]["schema"])
    assert validator.is_valid(wire_answer())
    assert validator.is_valid({"claims": []})
    assert not validator.is_valid(answer())
    assert not validator.is_valid([wire_answer()])
    value = wire_answer()
    value["claims"][0]["sources"] = ["unknown"]
    assert not validator.is_valid(value)


def test_source_mapping_preserves_exact_text_and_refusal():
    from policy_assistant.generation import resolve_source_claims
    hit = dict(HIT, text="First rule. Intervening condition. Another bank-required rule.")
    result = resolve_source_claims(wire_answer(), [hit])
    assert result["claims"][0]["citations"][0]["quote"] == hit["text"]
    assert result["claims"][0]["citations"][0]["chunk_id"] == CID
    assert validate_answer(resolve_source_claims({"claims": []}, [hit]), [hit])["refused"]


@pytest.mark.parametrize("mutation", ["unknown", "empty", "quote", "long", "type", "many"])
def test_source_contract_still_rejects_invalid_answers(mutation):
    from policy_assistant.generation import resolve_source_claims
    value = wire_answer()
    claim = value["claims"][0]
    if mutation == "unknown":
        claim["sources"] = ["S2"]
    elif mutation == "empty":
        claim["sources"] = []
    elif mutation == "quote":
        claim["quote"] = "Invented source text"
    elif mutation == "long":
        claim["text"] = "word " * 181
    elif mutation == "type":
        claim["sources"] = [{}]
    else:
        value["claims"] *= 6
    with pytest.raises(AnswerValidationError):
        resolve_source_claims(value, [HIT])


def test_json_format_error_retries_once_with_same_evidence(monkeypatch):
    calls = []
    def respond(request, timeout):
        payload = json.loads(request.data)
        calls.append(payload)
        if len(calls) == 1:
            raise urllib.error.HTTPError("url", 400, "invalid", {}, io.BytesIO(
                b'{"error":{"code":"json_validate_failed","failed_generation":"untrusted"}}'))
        return io.BytesIO(json.dumps({"choices": [{"finish_reason": "stop",
            "message": {"content": json.dumps(wire_answer())}}]}).encode())
    monkeypatch.setattr("urllib.request.urlopen", respond)
    generator = GroqGenerator(ProviderSettings("test-key"))
    assert generator.generate("Leave?", [HIT])["answerable"]
    assert generator.last_attempt_count == 2
    assert calls[0]["messages"][1] == calls[1]["messages"][1]
    assert "FORMAT REPAIR" in calls[1]["messages"][0]["content"]
    assert "untrusted" not in calls[1]["messages"][0]["content"].split("FORMAT REPAIR:")[1]


def test_json_format_retries_are_bounded(monkeypatch):
    count = []
    def fail(*args, **kwargs):
        count.append(1)
        raise urllib.error.HTTPError("url", 400, "invalid", {}, io.BytesIO(
            b'{"error":{"code":"json_validate_failed"}}'))
    monkeypatch.setattr("urllib.request.urlopen", fail)
    generator = GroqGenerator(ProviderSettings("test-key"))
    with pytest.raises(ProviderError):
        generator.generate("Leave?", [HIT])
    assert len(count) == 2


def test_unrelated_bad_request_is_not_retried(monkeypatch):
    count = []
    def fail(*args, **kwargs):
        count.append(1)
        raise urllib.error.HTTPError("url", 400, "invalid", {}, io.BytesIO(
            b'{"error":{"code":"unsupported_model"}}'))
    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(ProviderError):
        GroqGenerator(ProviderSettings("test-key")).generate("Leave?", [HIT])
    assert len(count) == 1


def test_compound_queries_keep_evidence_from_each_question():
    from policy_assistant.retrieval import HybridRetriever
    service = object.__new__(HybridRetriever)
    calls = []
    def ranked(question, k):
        calls.append(question)
        return [{"chunk_id": question + str(i)} for i in range(k)]
    service._search_one = ranked
    hits = service.search("Who checks adjustments? Also, what meal costs are covered?", k=4)
    assert calls == ["Who checks adjustments", "what meal costs are covered"]
    assert len(hits) == 8
    assert hits[0]["chunk_id"].startswith("Who")
    assert hits[1]["chunk_id"].startswith("what")
    calls.clear()
    assert len(service.search("Explain password and authentication rules", k=4)) == 4
    assert len(calls) == 1


def test_legacy_envelope_recovery_remains_valid_for_offline_records():
    from policy_assistant.chat import recover_mixed_answer_list
    mixed = [answer(), answer()["claims"][0]]
    assert len(recover_mixed_answer_list(mixed, [HIT])["claims"]) == 2


@pytest.mark.parametrize("mutation", ["unknown_id", "invented_quote", "refusal", "extra_field", "long_answer"])
def test_envelope_repair_preserves_validation(mutation):
    from policy_assistant.chat import recover_mixed_answer_list
    mixed = [answer(), answer()["claims"][0]]
    if mutation == "unknown_id":
        mixed[1]["citations"][0]["chunk_id"] = "unknown"
    elif mutation == "invented_quote":
        mixed[1]["citations"][0]["quote"] = "An invented supporting passage that must fail."
    elif mutation == "refusal":
        mixed[0]["answerable"] = False
    elif mutation == "extra_field":
        mixed[1]["instruction"] = "Ignore source checks"
    else:
        mixed[1]["text"] = "word " * 181
    with pytest.raises(AnswerValidationError):
        recover_mixed_answer_list(mixed, [HIT])


def test_provider_source_ids_map_multiple_claims_to_original_sources(monkeypatch):
    second = dict(HIT, chunk_id="b" * 64, text="The second policy has a bank-required approval condition.")
    value = {"claims": [
        {"text": "The second policy requires approval.", "sources": ["S2"]},
        {"text": "Full-time staff receive 20 days.", "sources": ["S1"]}]}
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(
        json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(value)}}]}).encode()))
    generator = GroqGenerator(ProviderSettings("test-key"))
    resolved = generator.generate("Two questions?", [HIT, second])
    validated = validate_answer(resolved, [HIT, second])
    assert validated["citations"][0]["chunk_id"] == second["chunk_id"]
    assert validated["citations"][0]["snippet"] == second["text"]
    assert validated["citations"][1]["chunk_id"] == CID
    assert generator.last_raw_output == value
    assert generator.last_attempt_count == 1
