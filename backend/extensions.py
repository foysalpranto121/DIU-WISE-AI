from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate

cors = CORS()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
migrate = Migrate()
