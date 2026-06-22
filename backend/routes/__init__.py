from .ai_routes import ai_bp
from .auth_routes import auth_bp
from .calendar_routes import calendar_bp
from .chat_routes import chat_bp
from .dashboard_routes import dashboard_bp
from .page_routes import pages_bp
from .user_routes import user_bp
from .voice_routes import voice_bp
from .voice_assistant_routes import va_bp
from .subscription_routes import sub_bp

__all__ = ["ai_bp", "auth_bp", "calendar_bp", "chat_bp", "dashboard_bp", "pages_bp", "user_bp", "voice_bp", "va_bp", "sub_bp"]
