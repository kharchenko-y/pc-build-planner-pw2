"""WSGI entry point for PythonAnywhere."""
from threading import Lock

from a2wsgi import ASGIMiddleware

from app import app

_adapter = None
_adapter_lock = Lock()


def application(environ, start_response):
    global _adapter
    if _adapter is None:
        with _adapter_lock:
            if _adapter is None:
                # uWSGI imports this module before forking its workers. Start
                # the ASGI event loop in the worker handling the first request.
                _adapter = ASGIMiddleware(app)
    return _adapter(environ, start_response)

