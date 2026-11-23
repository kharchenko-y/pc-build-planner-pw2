"""WSGI entry point for hosting that provides a persistent home directory."""
from a2wsgi import ASGIMiddleware

from app import app

application = ASGIMiddleware(app)

