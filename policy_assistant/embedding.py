"""Pinned local MiniLM embeddings with a project-local, integrity-checked cache."""
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import urllib.request

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
MODEL_SHA256 = "913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3"
MODEL_FILES = ("config.json", "model.onnx", "special_tokens_map.json",
               "tokenizer_config.json", "tokenizer.json", "vocab.txt")
DIMENSIONS = 384
MAX_TOKENS = 256


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def model_directory(root: Path) -> Path:
    return root / "data/cache/minilm"


def verify_model(root: Path) -> dict:
    cache = model_directory(root)
    try:
        record = json.loads((cache / "model-integrity.json").read_text(encoding="utf-8"))
        if record["archive_sha256"] != MODEL_SHA256 or set(record["files"]) != set(MODEL_FILES):
            raise ValueError("Unexpected model identity")
        for name, digest in record["files"].items():
            if file_hash(cache / "onnx" / name) != digest:
                raise ValueError(f"Model file checksum mismatch: {name}")
        return record
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Model cache is missing or incomplete. Run python -m scripts.prepare_model.") from exc


def prepare_model(root: Path) -> dict:
    """Only this explicit setup function accesses the model download URL."""
    cache = model_directory(root)
    cache.mkdir(parents=True, exist_ok=True)
    if (cache / "model-integrity.json").exists():
        return verify_model(root)
    archive = cache / "onnx.tar.gz"
    if not archive.exists() or file_hash(archive) != MODEL_SHA256:
        # An interrupted download never replaces a verified archive.
        with tempfile.NamedTemporaryFile(dir=cache, suffix=".download", delete=False) as temp:
            temp_path = Path(temp.name)
            try:
                with urllib.request.urlopen(MODEL_URL, timeout=90) as response:
                    for block in iter(lambda: response.read(1024 * 1024), b""):
                        temp.write(block)
                temp.flush()
            except Exception:
                temp.close()
                temp_path.unlink(missing_ok=True)
                raise
        if file_hash(temp_path) != MODEL_SHA256:
            temp_path.unlink(missing_ok=True)
            raise ValueError("Downloaded model does not match the pinned SHA-256.")
        temp_path.replace(archive)
    with tarfile.open(archive, "r:gz") as tar:
        # Extract only expected regular files; reject links and arbitrary archive paths.
        expected = {f"onnx/{name}" for name in MODEL_FILES}
        members = [m for m in tar.getmembers() if m.name in expected]
        if {m.name for m in members} != expected or any(not m.isfile() for m in members):
            raise ValueError("Model archive does not contain the expected regular files.")
        tar.extractall(cache, members=members, filter="data")
    record = {"model": MODEL_NAME, "archive_sha256": MODEL_SHA256,
              "dimensions": DIMENSIONS,
              "files": {name: file_hash(cache / "onnx" / name) for name in MODEL_FILES}}
    (cache / "model-integrity.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


class LocalEmbedding:
    def __init__(self, root: Path):
        # Imports are lazy: the Flask foundation can start before ingestion dependencies exist.
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        from tokenizers import Tokenizer
        self.identity = verify_model(root)
        cache = model_directory(root)
        self.function = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
        self.function.DOWNLOAD_PATH = cache
        self.tokenizer = Tokenizer.from_file(str(cache / "onnx/tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()

    def count(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=True).ids)

    def offsets(self, text: str) -> list[tuple[int, int]]:
        return self.tokenizer.encode(text, add_special_tokens=False).offsets

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("Embedding input must contain nonempty text.")
        if any(self.count(text) > MAX_TOKENS for text in texts):
            raise ValueError("Embedding input exceeds the 256-token model limit.")
        return [vector.tolist() for vector in self.function(texts)]
