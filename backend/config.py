import logging
import os
import secrets
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def is_development() -> bool:
    """Single place that decides whether this process is a local dev run.

    Anything that is not explicitly FLASK_ENV=development is treated as
    production, so a missing or misspelled variable fails safe.
    """
    return os.getenv("FLASK_ENV", "production").strip().lower() == "development"


def resolve_secret_key() -> str:
    """Return the session signing key, refusing to invent one in production.

    FIX: this defaulted to the literal string "change-this-in-production". Any
    deployment that forgot the variable signed its session cookies with a value
    published in the repo, so anyone could forge a session for any user.
    """
    key = os.getenv("SECRET_KEY", "").strip()
    if key and key != "change-this-in-production":
        return key

    if not is_development():
        raise RuntimeError(
            "SECRET_KEY is not set. Refusing to start with a guessable session "
            "key. Set SECRET_KEY in the environment (Render dashboard, or a "
            "local .env). Generate one with: "
            "python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Local development only. A fresh key per boot means sessions do not survive
    # a restart, which is a visible nuisance rather than a silent weak default.
    logger.warning(
        "SECRET_KEY is not set. Generating a throwaway key for this development "
        "run only. Existing logins will be invalidated on every restart."
    )
    return secrets.token_hex(32)

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

    DEVELOPMENT = is_development()
    DEBUG = DEVELOPMENT and os.getenv("FLASK_DEBUG", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    SECRET_KEY = resolve_secret_key()
    SESSION_COOKIE_HTTPONLY = True
    # FIX: was tightened to "Strict" in Phase 2, but Strict breaks Google
    # sign-in: the OAuth callback is a top level navigation arriving from
    # accounts.google.com, and under Strict the browser withholds the session
    # cookie on it, so the state stored in the session is unreadable and every
    # callback fails validation. Lax sends the cookie on top level GET
    # navigations, which is exactly the callback case, while still blocking
    # cookies on cross site POSTs and subresource requests. This remains a
    # partial CSRF mitigation only. See AGENT.md.
    SESSION_COOKIE_SAMESITE = "Lax"
    # Secure cookies need HTTPS, which local development does not have.
    SESSION_COOKIE_SECURE = not DEVELOPMENT

    # Cross-origin access is off unless an origin is named. This is a Flask
    # monolith serving its own templates, so the browser never makes a
    # cross-origin call to it in normal use.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]

    # Seeding the default admin is opt in. See factory.py.
    SEED_ADMIN = os.getenv("SEED_ADMIN", "").strip().lower() in ("1", "true", "yes")

    # Flask-Limiter. Defaults to in-process memory, which is correct for a
    # single Render instance; point RATELIMIT_STORAGE_URI at Redis if the app
    # is ever scaled past one worker process.
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_LOGIN = os.getenv("RATELIMIT_LOGIN", "10 per minute")
    RATELIMIT_CHAT = os.getenv("RATELIMIT_CHAT", "20 per minute")
    # Password reset requests send real email through Brevo's free tier
    # (300 per day), so this is deliberately tight.
    RATELIMIT_PASSWORD_RESET = os.getenv("RATELIMIT_PASSWORD_RESET", "5 per hour")

    # Brevo SMTP relay for password reset email (Flask-Mail settings).
    # The BREVO_* names are the team's convention; MAIL_DEFAULT_SENDER must be
    # a sender address verified in the Brevo dashboard.
    MAIL_SERVER = os.getenv("BREVO_SMTP_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.getenv("BREVO_SMTP_PORT", "587"))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("BREVO_SMTP_LOGIN", "")
    MAIL_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")
    # Without credentials Flask-Mail would raise on connect. Suppress instead,
    # so a misconfigured deploy logs a loud warning rather than 500ing the
    # forgot-password page. See PasswordResetService.
    MAIL_SUPPRESS_SEND = not (MAIL_USERNAME and MAIL_PASSWORD)

    # How long a password reset link stays valid, in seconds.
    PASSWORD_RESET_MAX_AGE = int(os.getenv("PASSWORD_RESET_MAX_AGE", "3600"))

    # Google OAuth 2.0. Both values come from the Google Cloud Console app the
    # team registers; sign-in is disabled cleanly when they are unset.
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(BASE_DIR, "ai_engine", "trained"))
    KNOWLEDGE_FILE = os.getenv(
        "KNOWLEDGE_FILE", os.path.join(BASE_DIR, "data", "wellness_knowledge.txt")
    )
