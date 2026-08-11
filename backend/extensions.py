from authlib.integrations.flask_client import OAuth
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

cors = CORS()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
migrate = Migrate()
mail = Mail()
oauth = OAuth()

# No default_limits: only the routes that are explicitly decorated are limited,
# so adding this cannot change the behaviour of any other endpoint.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
