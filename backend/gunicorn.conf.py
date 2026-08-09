"""Gunicorn settings for the Render deployment.

Every value is read from the environment so the same file works on any
instance type without editing. The defaults suit one small instance.

Two of these matter more than the rest:

`workers` defaults to 1 because booting the app loads a sentence-transformers
model, a scikit-learn model and the transformers runtime into memory. Each
extra worker is another full copy of that, and the app does not fit in 512 MB
even once.

`timeout` is well above the gunicorn default of 30 seconds because the first
request after a cold start can arrive while those models are still loading.
"""

import os


def _int_from_env(name: str, default: int) -> int:
    """Read an integer setting, falling back to the default if it is unusable."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = _int_from_env("WEB_CONCURRENCY", 1)
threads = _int_from_env("GUNICORN_THREADS", 4)
timeout = _int_from_env("GUNICORN_TIMEOUT", 180)
graceful_timeout = _int_from_env("GUNICORN_GRACEFUL_TIMEOUT", 30)

# Load the app in the worker, not the arbiter, so the port is bound before the
# slow model imports begin. Render's health check gives up on a service that
# takes too long to start listening.
preload_app = False

# Render collects stdout and stderr, so log to the streams rather than files.
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
