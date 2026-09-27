"""Run the foundation with Waitress on Windows, macOS, or Linux."""

import logging

from waitress import serve

from policy_assistant import create_app
from policy_assistant.config import Settings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_environment()
    logging.info("Starting Lumen Vale foundation on %s:%s (RAG not implemented)",
                 settings.host, settings.port)
    serve(create_app(settings), host=settings.host, port=settings.port, threads=4)


if __name__ == "__main__":
    main()
