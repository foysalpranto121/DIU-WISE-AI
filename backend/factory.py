import os
import secrets

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from dotenv import load_dotenv

load_dotenv()

from ai_engine.burnout_model import BurnoutModel
from ai_engine.distress_detector import DistressDetector
from ai_engine.emotion_classifier import EmotionClassifier
from ai_engine.rag_engine import RAGEngine
from ai_engine.agent_router import AgentRouter
from config import Config
from models import User, db, Appointment
from routes import ai_bp, auth_bp, calendar_bp, chat_bp, dashboard_bp, pages_bp, user_bp, voice_bp, va_bp, sub_bp
from services.data_service import DataService
from services.triage_service import TriageService
from services.notification_service import NotificationService
from extensions import cors, limiter, login_manager, migrate, oauth
from services.password_reset_service import PasswordResetService
from services.registry import ServiceRegistry


def _seed_default_admin(app):
    """Create the platform admin account, but only when asked to.

    FIX: this used to run on every boot and always set the same password,
    `Admin@12345`, on `admin@diu-wise.ai`. A deployed instance therefore shipped
    with publicly known admin credentials. Seeding is now opt in via
    SEED_ADMIN=true, and the password comes from SEED_ADMIN_PASSWORD. If that is
    not supplied, a random one is generated and written to the log once, so
    there is no fixed credential anywhere in the code or the database.
    """
    if not app.config["SEED_ADMIN"]:
        return
    if User.query.filter_by(email="admin@diu-wise.ai").first() is not None:
        return

    password = os.getenv("SEED_ADMIN_PASSWORD", "").strip()
    generated = not password
    if generated:
        password = secrets.token_urlsafe(18)

    admin = User(
        full_name="Platform Admin",
        email="admin@diu-wise.ai",
        role="admin",
        is_active_account=True,
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    if generated:
        app.logger.warning(
            "Seeded admin@diu-wise.ai with a generated password: %s\n"
            "This is shown once and is not recoverable. Change it after first "
            "login, and unset SEED_ADMIN.",
            password,
        )
    else:
        app.logger.info("Seeded admin@diu-wise.ai from SEED_ADMIN_PASSWORD.")


def _tables_ready(app) -> bool:
    """True once `flask db upgrade` has created the schema.

    Schema creation is owned by Alembic now, so booting against an empty
    database is a setup mistake rather than something the app should paper over.
    Seeding is skipped with a clear message instead of raising a driver error.
    """
    from sqlalchemy import inspect

    if inspect(db.engine).has_table("users"):
        return True
    app.logger.warning(
        "Database schema is missing. Run 'flask --app manage db upgrade' "
        "before starting the app; skipping seed."
    )
    return False


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    # FIX: cors.init_app(app) with no arguments allows every origin. This is a
    # same-origin monolith, so nothing is allowed unless CORS_ORIGINS names it.
    cors.init_app(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    limiter.init_app(app)
    db.init_app(app)
    # FIX: schema was created by db.create_all() on every boot, which silently
    # diverges from the models over time and cannot express column changes.
    # Alembic owns the schema now; render_as_batch keeps the SQLite fallback
    # usable for ALTER TABLE style migrations.
    migrate.init_app(app, db, render_as_batch=True)
    oauth.init_app(app)
    if app.config["GOOGLE_CLIENT_ID"]:
        # Discovery metadata gives Authlib the endpoints plus Google's JWKS for
        # id_token verification. The openid scope makes Authlib generate and
        # check a nonce alongside the state parameter.
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    if not app.config["BREVO_API_KEY"]:
        app.logger.warning(
            "BREVO_API_KEY is not set; password reset emails will not be "
            "sent. Set it in the environment."
        )

    # Seed Database inside app context (tables come from 'flask db upgrade')
    with app.app_context():
        if _tables_ready(app):
            _seed_default_admin(app)

    # Configure Authentication
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        # FIX: User.query.get() is the legacy SQLAlchemy 1.x API and is
        # deprecated in 2.x. A non-numeric cookie value also raised ValueError
        # here instead of being treated as a failed lookup.
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        api_prefixes = ("/api/", "/dashboard-data", "/predict", "/emotion",
                        "/chat", "/generate-plan", "/voice-journal/transcribe",
                        "/voice-journal/save", "/voice-journal/entries")
        if request.path.startswith(api_prefixes):
            return jsonify({"error": "authentication required"}), 401
        if request.headers.get("Accept", "").find("application/json") >= 0:
            return jsonify({"error": "authentication required"}), 401
        return redirect(url_for("auth.login"))

    # Initialize & Register services inside ServiceRegistry
    burnout_model = BurnoutModel(model_dir=app.config["MODEL_DIR"])
    burnout_model.load_or_train()
    ServiceRegistry.register("burnout_model", burnout_model)

    distress_detector = DistressDetector()
    ServiceRegistry.register("distress_detector", distress_detector)

    emotion_classifier = EmotionClassifier()
    ServiceRegistry.register("emotion_classifier", emotion_classifier)

    rag_engine = RAGEngine(
        knowledge_file=app.config["KNOWLEDGE_FILE"], model_dir=app.config["MODEL_DIR"]
    )
    ServiceRegistry.register("rag_engine", rag_engine)

    agent_router = AgentRouter()
    ServiceRegistry.register("agent_router", agent_router)

    triage_service = TriageService()
    ServiceRegistry.register("triage_service", triage_service)

    notification_service = NotificationService()
    ServiceRegistry.register("notification_service", notification_service)

    data_service = DataService()
    ServiceRegistry.register("data_service", data_service)

    password_reset_service = PasswordResetService()
    ServiceRegistry.register("password_reset_service", password_reset_service)

    with app.app_context():
        if _tables_ready(app):
            data_service.seed_if_empty()

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(va_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(sub_bp)

    # Core Routes
    @app.route("/", methods=["GET"])
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("subscription.landing"))
        return render_template("index.html")

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "DIU WISE backend"})

    return app
