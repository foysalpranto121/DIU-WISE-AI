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
from models import User, db
from routes import ai_bp, auth_bp, chat_bp, dashboard_bp, user_bp, pages_bp
from services.data_service import DataService
from services.triage_service import TriageService
from extensions import cors, login_manager
from services.registry import ServiceRegistry


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    cors.init_app(app)
    db.init_app(app)

    # Seed Database & Create tables inside app context
    with app.app_context():
        db.create_all()
        if User.query.filter_by(email="admin@diu-wise.ai").first() is None:
            admin = User(
                full_name="Platform Admin",
                email="admin@diu-wise.ai",
                role="admin",
                is_active_account=True,
            )
            admin.set_password("Admin@12345")
            db.session.add(admin)
            db.session.commit()

    # Configure Authentication
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/dashboard-data") or request.path.startswith("/predict") or request.path.startswith("/emotion"):
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

    data_service = DataService()
    ServiceRegistry.register("data_service", data_service)

    with app.app_context():
        data_service.seed_if_empty()

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(pages_bp)

    # Core Routes
    @app.route("/", methods=["GET"])
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return render_template("index.html")

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "DIU WISE backend"})

    return app
