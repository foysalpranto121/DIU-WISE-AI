import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SQLITE_FALLBACK_URI = (
    f"sqlite:///{os.path.join(BASE_DIR, 'diu_wise.db').replace(os.sep, '/')}"
)


def normalize_database_url(url: str) -> str:
    """Make an externally supplied DATABASE_URL usable by this app.

    Neon (and most managed Postgres providers) hand out URLs in the
    `postgres://` or `postgresql://` form. Both need adjusting before
    SQLAlchemy can use them here:

    1. `postgres://` is not a scheme SQLAlchemy recognises at all.
    2. Bare `postgresql://` resolves to the psycopg2 driver, but this project
       installs `psycopg[binary]` (psycopg 3), so the DSN has to say
       `postgresql+psycopg://` explicitly.
    3. Neon requires TLS, so `sslmode=require` is added when the caller did not
       already specify an sslmode.
    """
    if not url or not url.startswith(("postgres://", "postgresql://", "postgresql+")):
        return url

    parts = urlsplit(url)

    # FIX: "postgres://" and bare "postgresql://" both fail at runtime here.
    # The first is not a valid SQLAlchemy scheme, the second selects psycopg2
    # which is not in requirements.txt, so it raised ModuleNotFoundError.
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+psycopg"

    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault("sslmode", "require")

    # channel_binding is a Neon convenience parameter that psycopg accepts but
    # that adds nothing here, so it is left exactly as the provider supplied it.
    return urlunsplit(
        (scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


class Config:
    BASE_DIR = BASE_DIR
    # Production uses PostgreSQL via DATABASE_URL; local demo falls back to SQLite
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv("DATABASE_URL", SQLITE_FALLBACK_URI)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Neon suspends idle compute, so a pooled connection can be dead by the time
    # it is handed back out. pool_pre_ping discards those instead of raising.
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True, "pool_recycle": 300}
        if SQLALCHEMY_DATABASE_URI.startswith("postgresql")
        else {}
    )

    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(BASE_DIR, "ai_engine", "trained"))
    KNOWLEDGE_FILE = os.getenv(
        "KNOWLEDGE_FILE", os.path.join(BASE_DIR, "data", "wellness_knowledge.txt")
    )
