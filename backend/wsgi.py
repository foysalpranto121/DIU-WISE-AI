"""WSGI entry point for production servers.

Render starts the app through this module (`gunicorn wsgi:app`). It is kept
separate from `app.py` so the production server never imports that module's
development `app.run(...)` block.
"""

from factory import create_app

app = create_app()
