import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # Production uses PostgreSQL via DATABASE_URL; local demo falls back to SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'diu_wise.db').replace(os.sep, '/')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(BASE_DIR, "ai_engine", "trained"))
    KNOWLEDGE_FILE = os.getenv(
        "KNOWLEDGE_FILE", os.path.join(BASE_DIR, "data", "wellness_knowledge.txt")
    )
