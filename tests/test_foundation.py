import json
import shutil

import pytest

from policy_assistant import create_app
from policy_assistant.config import PROJECT_ROOT, Settings
from policy_assistant.corpus import CorpusError, verify_corpus


@pytest.fixture
def source_copy(tmp_path):
    shutil.copytree(PROJECT_ROOT / "corpus", tmp_path / "corpus")
    shutil.copy2(PROJECT_ROOT / "corpus-manifest.json", tmp_path / "corpus-manifest.json")
    return tmp_path


def client_for(root):
    return create_app(Settings(root, "127.0.0.1", 8000, 42)).test_client()


def test_health_verifies_real_corpus_without_claiming_rag_readiness():
    response = client_for(PROJECT_ROOT).get("/health")
    assert response.status_code == 200
    assert response.json["corpus"]["documents"] == 12
    assert response.json["corpus"]["status"] == "verified"
    assert response.json["rag_ready"] is False


def test_home_explains_current_state():
    response = client_for(PROJECT_ROOT).get("/")
    assert response.status_code == 200
    assert b"Question answering is not available yet" in response.data


@pytest.mark.parametrize("mutation", ["changed", "missing", "extra"])
def test_changed_missing_or_extra_source_fails_health(source_copy, mutation):
    source = next((source_copy / "corpus").glob("*.md"))
    if mutation == "changed":
        source.write_text("Changed policy", encoding="utf-8")
    elif mutation == "missing":
        source.unlink()
    else:
        (source_copy / "corpus" / "gold-answers.md").write_text("Not a policy")
    response = client_for(source_copy).get("/health")
    assert response.status_code == 503
    assert response.json["corpus"]["status"] == "invalid"
    assert str(source_copy).encode() not in response.data


@pytest.mark.parametrize("path", ["../evaluation/questions.jsonl", "evaluation/gold.md", "/tmp/a.md", "corpus/../../gold.md"])
def test_manifest_cannot_include_evaluation_or_external_paths(source_copy, path):
    manifest_path = source_copy / "corpus-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["documents"][0]["path"] = path
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CorpusError):
        verify_corpus(source_copy)


def test_duplicate_document_id_is_rejected(source_copy):
    path = source_copy / "corpus-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["documents"][1]["document_id"] = manifest["documents"][0]["document_id"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CorpusError, match="Duplicate"):
        verify_corpus(source_copy)


@pytest.mark.parametrize("value", ["not-a-port", "0", "65536"])
def test_invalid_port_is_rejected(monkeypatch, tmp_path, value):
    monkeypatch.setenv("APP_PORT", value)
    with pytest.raises(ValueError, match="APP_PORT"):
        Settings.from_environment(tmp_path)


def test_environment_overrides_dotenv(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("APP_PORT=9999\n", encoding="utf-8")
    monkeypatch.setenv("APP_PORT", "8123")
    assert Settings.from_environment(tmp_path).port == 8123
