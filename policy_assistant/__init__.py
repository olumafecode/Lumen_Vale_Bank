"""Application foundation. Retrieval and generation are added in later stages."""

import random

from flask import Flask, jsonify, render_template

from .config import Settings
from .corpus import CorpusError, verify_corpus


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_environment()
    random.seed(settings.random_seed)
    app = Flask(__name__)
    app.config.update(SETTINGS=settings, MAX_CONTENT_LENGTH=16 * 1024)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        # Recheck the small corpus so missing/changed files do not produce a green check.
        try:
            corpus = verify_corpus(settings.project_root)
        except CorpusError:
            app.logger.warning("Canonical corpus verification failed")
            return jsonify(status="error", stage=2, service="lumen-vale-policy-assistant",
                           rag_ready=False, corpus={"status": "invalid"}), 503
        return jsonify(status="ok", stage=2, service="lumen-vale-policy-assistant",
                       rag_ready=False, corpus=corpus)

    return app
