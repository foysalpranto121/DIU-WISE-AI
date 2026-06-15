from .ai_routes import ai_bp
from .auth_routes import auth_bp
from .chat_routes import chat_bp
from .dashboard_routes import dashboard_bp
from .user_routes import user_bp
from .page_routes import pages_bp

__all__ = ["ai_bp", "chat_bp", "dashboard_bp", "auth_bp", "user_bp", "pages_bp"]
