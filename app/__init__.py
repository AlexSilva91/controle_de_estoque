from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_login import LoginManager

from .models import db
from .routes import init_app
from app.models.entities import Usuario

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    # Configura Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    init_app(app)

    return app
