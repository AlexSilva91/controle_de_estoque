from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
from .models import db
from .routes import init_app
from app.models.entities import Usuario

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Carrega a configuração apropriada
    app.config.from_object(config[config_name])

    # Inicializa banco e migrações
    db.init_app(app)
    Migrate(app, db)

    # Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Rotas
    init_app(app)

    return app