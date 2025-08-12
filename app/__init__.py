import time
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, g, send_from_directory
from flask_migrate import Migrate
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from config import config
from .models import db
from .routes import init_app
from app.models.entities import Usuario
import os

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.jinja_env.cache = {}

    configure_logging(app)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    init_app(app)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
        
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app


def configure_logging(app):
    """Configura logging global com access log e tratamento diferenciado de erros."""

    log_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)
    
    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        duration = round(time.time() - getattr(g, 'start_time', time.time()), 4)
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        method = request.method
        path = request.path
        status = response.status_code
        size = response.calculate_content_length() or 0

        app.logger.info(f'{ip} "{method} {path}" {status} {size}B {duration}s')

        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            if request.path == '/favicon.ico':
                return '', 204  

            app.logger.warning(f"HTTP {e.code} em {request.path}: {e.description}")
            return e

        app.logger.exception("Erro não tratado:")
        return "Erro interno no servidor", 500
