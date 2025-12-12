import os
import time
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, abort, request, g, send_from_directory, render_template
from flask_migrate import Migrate
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from config import config
from app.models.entities import Usuario
from app.models import db
from .routes import init_app

def configure_logging(app):
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
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

        request_data = {
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "json": request.get_json(silent=True)
        }

        try:
            response_body = response.get_data(as_text=True)
            if len(response_body) > 1000:
                response_body = response_body[:1000] + "...[truncated]"
        except Exception:
            response_body = "<não capturado>"

        extra = {
            "ip": ip,
            "method": method,
            "path": path,
            "status": status,
            "duration_s": duration,
            "request": request_data,
            "response": response_body,
            "size_bytes": size
        }

        app.logger.info(f'{method} {path} {status}', extra={'extra_data': extra})
        return response

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

    from app.models import audit_events
    with app.app_context():
        audit_events.setup_audit_events()

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

    @app.errorhandler(400)
    def bad_request_error(e):
        app.logger.warning(f"400 Bad Request em {request.path}: {e}")
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        app.logger.warning(f"403 Forbidden em {request.path}: {e}")
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(e):
        app.logger.warning(f"404 Not Found em {request.path}: {e}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception(f"500 Internal Server Error em {request.path}: {e}")
        return render_template("errors/500.html"), 500

    @app.errorhandler(ConnectionError)
    @app.errorhandler(OSError)
    @app.errorhandler(TimeoutError)
    def service_unavailable_error(e):
        app.logger.error(f"Serviço indisponível: {e}")
        return render_template("errors/503.html"), 503

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            if request.path == '/favicon.ico':
                return '', 204
            app.logger.warning(f"HTTP {e.code} em {request.path}: {e.description}")
            return e

        app.logger.exception("Erro não tratado:")
        return render_template("errors/500.html"), 500

    @app.route("/test-400")
    def test_400():
        abort(400, description="Teste de Bad Request")

    @app.route("/test-403")
    def test_403():
        abort(403, description="Teste de Forbidden")

    @app.route("/test-404")
    def test_404():
        abort(404, description="Teste de Not Found")

    @app.route("/test-500")
    def test_500():
        raise Exception("Teste de Internal Server Error")

    @app.route("/test-503")
    def test_503():
        raise ConnectionError("Teste de Serviço Indisponível")

    return app