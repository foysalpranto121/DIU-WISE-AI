"""Migration entrypoint for Alembic / Flask-Migrate.

Usage from the `backend/` directory, with DATABASE_URL set in `.env`:

    flask --app manage db upgrade        # apply migrations
    flask --app manage db migrate -m "…" # autogenerate a new revision
    flask --app manage db current        # show the applied revision

This builds a stripped down app that wires up only the config, the models and
Migrate. `factory.create_app()` also registers Migrate, so `flask --app factory`
works too, but that path loads the AI engine (sentence-transformers, the burnout
model) on import, which schema commands have no use for.
"""

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from config import Config

# Every model has to be imported for autogenerate to see it, even though only
# `db` is referenced below.
from models import (  # noqa: F401
    AcademicEvent,
    Appointment,
    StudentMetric,
    Subscription,
    User,
    VoiceJournal,
    db,
)
from extensions import migrate


def create_migration_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    return app


app = create_migration_app()
