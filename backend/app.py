import os

from factory import create_app

app = create_app()

if __name__ == "__main__":
    # FIX: this ran with debug=True unconditionally, which exposes the
    # interactive Werkzeug console. Anyone who can reach a traceback page on a
    # debug server can execute arbitrary Python on the host. Debug now follows
    # FLASK_ENV/FLASK_DEBUG (see config.py) and defaults to off.
    debug = app.config["DEBUG"]
    # Binding to 0.0.0.0 is only needed where something else fronts the app.
    host = os.getenv("HOST", "0.0.0.0" if not app.config["DEVELOPMENT"] else "127.0.0.1")
    app.run(host=host, port=int(os.getenv("PORT", 5000)), debug=debug, use_debugger=debug)
