"""WSGI entry point. Importing this module never calls an LLM or downloads a model."""

from policy_assistant import create_app

app = create_app()
