"""Policy chat application with local retrieval and cited Groq generation."""
import random
import re
import threading
import time

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from .config import Settings
from .corpus import CorpusError, verify_corpus
from .indexing import index_status
from .generation import GroqGenerator, ProviderSettings, ProviderError
from .retrieval import HybridRetriever
from .chat import validate_answer, AnswerValidationError, PROMPT_VERSION


def create_app(settings: Settings | None = None, *, generator=None, retriever_factory=None) -> Flask:
    settings = settings or Settings.from_environment()
    random.seed(settings.random_seed)
    app = Flask(__name__)
    provider = ProviderSettings.from_environment()
    generator = generator or GroqGenerator(provider)
    factory = retriever_factory or HybridRetriever
    state = {"retriever": None}
    lock = threading.Lock()
    app.config.update(SETTINGS=settings, MAX_CONTENT_LENGTH=16 * 1024)

    def retriever():
        if state["retriever"] is None:
            state["retriever"] = factory(settings.project_root)
        return state["retriever"]

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if request.path in ("/chat", "/health"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_):
        return jsonify(error="Request too large. Use a question of at most 1,200 characters."), 413

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        try:
            corpus = verify_corpus(settings.project_root)
        except CorpusError:
            return jsonify(status="error", stage=4, rag_ready=False,
                           corpus={"status": "invalid"}), 503
        idx = index_status(settings.project_root)
        local_ready = False
        if idx["ready"] and lock.acquire(blocking=False):
            try:
                retriever().check_fresh()
                local_ready = True
            except Exception:
                state["retriever"] = None
            finally:
                lock.release()
        return jsonify(status="ok", stage=4, service="lumen-vale-policy-assistant",
                       corpus=corpus, index=idx, local_retrieval_ready=local_ready,
                       provider={"name": "groq", "configured": provider.configured,
                                 "model": provider.model, "connection": "not_checked"},
                       rag_ready=local_ready and provider.configured)

    @app.post("/chat")
    def chat():
        if not request.is_json:
            return jsonify(error="Send application/json with a question field."), 415
        try:
            body = request.get_json()
        except BadRequest:
            return jsonify(error="Invalid JSON body."), 400
        question = body.get("question") if isinstance(body, dict) else None
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1200:
            return jsonify(error="Enter a question between 1 and 1,200 characters."), 400
        question = question.strip()
        if not generator.settings.configured:
            return jsonify(error="Add GROQ_API_KEY to the local .env file and restart the server."), 503
        if not lock.acquire(blocking=False):
            return jsonify(error="The assistant is answering another request. Please retry shortly."), 429
        start = time.perf_counter()
        try:
            service = retriever()
            # Reject overlong tokenizer input as a user error before retrieval or network access.
            if service.embedding.count(question) > 256:
                return jsonify(error="Please shorten your question to at most 256 model tokens."), 400
            hits = service.search(question, k=4)
            if not hits:
                raw = {"answerable": False}
            else:
                raw = generator.generate(question, hits)
            # Source edits during generation must not release stale citations.
            service.check_fresh()
            result = validate_answer(raw, hits)
            result.update(latency_ms=round((time.perf_counter() - start) * 1000, 1),
                          model=provider.model, prompt_version=PROMPT_VERSION,
                          provider_attempts=getattr(generator, "last_attempt_count", 1),
                          index_fingerprint=service.record["fingerprint"])
            return jsonify(result)
        except ProviderError as exc:
            return jsonify(error=str(exc), provider_attempts=getattr(generator, "last_attempt_count", 1)), exc.status
        except AnswerValidationError:
            return jsonify(error="The model answer failed citation checks. Please retry or rephrase.",
                           provider_attempts=getattr(generator, "last_attempt_count", 1)), 502
        except (CorpusError, ValueError, OSError):
            state["retriever"] = None
            return jsonify(error="Local policy data or index is unavailable or changed. Verify sources, rebuild the index, and restart."), 503
        except Exception:
            # Do not log exception payloads, questions, credentials, or provider responses.
            return jsonify(error="The assistant could not complete this request. Please retry."), 500
        finally:
            lock.release()

    @app.get("/sources/<chunk_id>")
    def source(chunk_id):
        if not re.fullmatch(r"[a-f0-9]{64}", chunk_id):
            return jsonify(error="Source not found."), 404
        if not lock.acquire(blocking=False):
            return jsonify(error="Assistant busy. Retry shortly."), 429
        try:
            hit = retriever().source(chunk_id)
            if hit is None:
                return jsonify(error="Source not found."), 404
            return render_template("source.html", hit=hit)
        except Exception:
            state["retriever"] = None
            return jsonify(error="Source index unavailable. Rebuild and restart."), 503
        finally:
            lock.release()

    return app
