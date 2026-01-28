from datetime import datetime
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
from app.models import db, audit_events
from app.utils.format_data_moeda import (
    format_currency,
    formatar_data_br,
    formatar_data_br2,
)
from .routes import init_app
from app.security import security
import json
import werkzeug.serving
import flask

BASEDIR = os.path.abspath(os.path.dirname(__file__))


# ==========================
# MONKEY PATCH DEFINITIVO PARA REMOVER SERVER HEADER
# ==========================
def apply_server_header_fix():
    """
    Aplica monkey patch no Werkzeug e Flask para nunca enviar Server header.
    Esta função DEVE ser chamada ANTES de criar o app Flask.
    """
    
    # ============================================
    # 1. PATCH NO WSGIRequestHandler DO WERKZEUG
    # ============================================
    class NoServerHeaderWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
        """Request Handler que NÃO envia Server header"""
        
        def send_response(self, code, message=None):
            """Envia resposta sem Server header"""
            super().send_response(code, message)
            
            # Remove Server header ANTES de enviar
            if 'Server' in self.headers:
                del self.headers['Server']
        
        def version_string(self):
            """Override para retornar string de versão vazia"""
            return ""
        
        def log_request(self, code='-', size='-'):
            """Override do logging simplificado"""
            if hasattr(self, 'log'):
                self.log('info', '"%s" %s %s',
                        self.requestline, str(code), str(size))
    
    # Aplica o patch globalmente
    werkzeug.serving.WSGIRequestHandler = NoServerHeaderWSGIRequestHandler
    
    # ============================================
    # 2. PATCH NA CLASSE Response DO WERKZEUG
    # ============================================
    from werkzeug.wrappers import Response
    
    original_response_init = Response.__init__
    
    def patched_response_init(self, *args, **kwargs):
        # Chama o construtor original
        original_response_init(self, *args, **kwargs)
        
        # Remove Server header imediatamente após criação
        self.headers.pop('Server', None)
        self.headers.pop('X-Powered-By', None)
    
    Response.__init__ = patched_response_init
    
    # ============================================
    # 3. PATCH NO make_response DO FLASK
    # ============================================
    original_make_response = flask.make_response
    
    def patched_make_response(*args, **kwargs):
        response = original_make_response(*args, **kwargs)
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        return response
    
    flask.make_response = patched_make_response
    
    return True


# ==========================
# LOGGING
# ==========================
def configure_logging(app: Flask):
    os.makedirs(os.path.join(BASEDIR, "logs"), exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        os.path.join(BASEDIR, "logs/app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
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

    # ==========================
    # REQUEST LOGGING
    # ==========================
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        duration = round(time.time() - getattr(g, "start_time", time.time()), 4)
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        method = request.method
        path = request.path
        status = response.status_code
        size = response.calculate_content_length() or 0

        request_data = {
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "json": request.get_json(silent=True),
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
            "size_bytes": size,
        }

        app.logger.info(f"{method} {path} {status}", extra={"extra_data": extra})
        return response


# ==========================
# UPLOADS
# ==========================
def create_upload_folders(app: Flask):
    """
    Cria automaticamente todas as pastas necessárias para upload de arquivos
    no diretório raiz (fora da pasta app).
    """
    try:
        upload_base = app.config.get("UPLOAD_BASE_DIR")
        
        if not upload_base:
            upload_base = os.path.join(app.static_folder, "uploads")
            app.logger.warning("UPLOAD_BASE_DIR não configurado, usando diretório antigo")

        folders_to_create = [
            upload_base,
            app.config.get("UPLOAD_FOLDER", os.path.join(upload_base, "produtos")),
            app.config.get("AVATAR_FOLDER", os.path.join(upload_base, "avatars")),
            app.config.get("DOCS_FOLDER", os.path.join(upload_base, "docs")),
            app.config.get("TEMP_FOLDER", os.path.join(upload_base, "temp")),
            os.path.join(upload_base, "logs", "uploads"),
        ]

        for folder in folders_to_create:
            try:
                os.makedirs(folder, exist_ok=True)
                app.logger.info(f"Pasta criada/verificada: {folder}")
            except Exception as e:
                app.logger.error(f"Erro ao criar pasta {folder}: {e}")

        test_file = os.path.join(upload_base, "test_write.txt")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            app.logger.info("Permissões de escrita verificadas com sucesso")
        except Exception as e:
            app.logger.warning(
                f"Aviso: Problema com permissões de escrita nas pastas de upload: {e}"
            )

        return True

    except Exception as e:
        app.logger.error(f"Erro crítico ao criar pastas de upload: {e}")
        return False


# ==========================
# APPLICATION FACTORY
# ==========================
def create_app(config_name="development") -> Flask:
    # ==========================
    # APLICA FIX DO SERVER HEADER ANTES DE CRIAR O APP
    # ==========================
    apply_server_header_fix()
    
    # Cria o app Flask
    app = Flask(__name__)
    
    # Log imediatamente após criar o app
    temp_logger = logging.getLogger(__name__)
    temp_logger.info("✅ Monkey patch aplicado: Server header será removido")
    
    # Configurações
    app.config.from_object(config[config_name])
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config['SERVER_NAME'] = None 
    app.jinja_env.cache = {}
    app.jinja_env.filters["moeda_br"] = format_currency
    app.jinja_env.filters["data_br"] = formatar_data_br
    app.jinja_env.filters["data_br2"] = formatar_data_br2

    # Logging
    configure_logging(app)

    # Banco de dados
    db.init_app(app)
    Migrate(app, db)

    # Pastas de upload
    with app.app_context():
        create_upload_folders(app)
        audit_events.setup_audit_events()

    # Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Rotas principais
    init_app(app)
    
    # ==========================
    # MIDDLEWARES DE SEGURANÇA (ORDEM CRÍTICA)
    # Flask executa @app.after_request na ORDEM INVERSA de definição
    # ==========================
    
    # 1. Cache headers (definido PRIMEIRO, executado ÚLTIMO)
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    # 2. Módulo de segurança
    security.init_app(app, features=['headers'])
    
    # 3. Middleware final para garantia (definido ÚLTIMO, executado PRIMEIRO)
    @app.after_request
    def final_security_check(response):
        """Garantia final - remove qualquer header que tenha escapado"""
        # Remove headers que expõem informações
        headers_to_remove = ['Server', 'X-Powered-By', 'X-Runtime']
        for header in headers_to_remove:
            response.headers.pop(header, None)
        
        # Verifica se todos os headers de segurança estão presentes
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
        }
        
        for header, value in required_headers.items():
            if response.headers.get(header) != value:
                response.headers[header] = value
        
        # Garante CSP
        if not response.headers.get('Content-Security-Policy'):
            csp_parts = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: blob:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'self'",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response.headers['Content-Security-Policy'] = '; '.join(csp_parts)
        
        return response

    # Favicon
    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    # Uploads públicos
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        upload_base = app.config.get("UPLOAD_BASE_DIR", os.path.join(app.static_folder, "uploads"))
        return send_from_directory(upload_base, filename)

    # Rotas de teste
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

    # Status uploads
    @app.route("/api/upload-status")
    def upload_status():
        upload_base = os.path.join(app.static_folder, "uploads")
        status = {
            "upload_base": {
                "path": upload_base,
                "exists": os.path.exists(upload_base),
                "writable": (
                    os.access(upload_base, os.W_OK)
                    if os.path.exists(upload_base)
                    else False
                ),
            },
            "subfolders": {},
        }

        subfolders = ["produtos", "avatars", "docs", "temp"]
        for folder in subfolders:
            folder_path = os.path.join(upload_base, folder)
            status["subfolders"][folder] = {
                "path": folder_path,
                "exists": os.path.exists(folder_path),
                "writable": (
                    os.access(folder_path, os.W_OK)
                    if os.path.exists(folder_path)
                    else False
                ),
            }

        return json.dumps(status, indent=2)

    @app.route('/security-test')
    def security_test():
        """Rota para testar headers de segurança - retorna JSON correto"""
        from flask import jsonify, request
        import json
        
        # Faz uma requisição interna para verificar os headers
        with app.test_client() as client:
            test_response = client.get('/')
        
        security_info = {
            'test': 'Security Headers Verification',
            'timestamp': datetime.now().isoformat(),
            'note': 'Check actual response headers with: curl -I http://localhost:5000',
            'expected_headers': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN', 
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
                'Content-Security-Policy': 'Present',
                'Server': 'Hidden (should not appear)',
                'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0, private',
            },
            'actual_headers_from_root': dict(test_response.headers),
            'your_request': {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'method': request.method,
                'path': request.path,
            },
            'security_score': {
                'total_headers': 8,
                'present_headers': sum(1 for h in [
                    'X-Content-Type-Options',
                    'X-Frame-Options', 
                    'X-XSS-Protection',
                    'Referrer-Policy',
                    'Permissions-Policy',
                    'Content-Security-Policy',
                    'Cache-Control'
                ] if test_response.headers.get(h)),
                'server_exposed': 'Server' in test_response.headers
            }
        }
        
        # Retorna como JSON correto usando jsonify
        return jsonify(security_info)

    @app.context_processor
    def inject_security_status():
        """Injeta status de segurança no template (apenas para admin)"""
        def check_security_headers():
            from flask import request
            return {
                'X-Content-Type-Options': request.headers.get('X-Content-Type-Options'),
                'X-Frame-Options': request.headers.get('X-Frame-Options'),
                'X-XSS-Protection': request.headers.get('X-XSS-Protection'),
                'Content-Security-Policy': request.headers.get('Content-Security-Policy'),
            }
        
        return dict(security_headers=check_security_headers)
    
    # ==========================
    # ERROR HANDLERS
    # ==========================
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
            if request.path == "/favicon.ico":
                return "", 204
            app.logger.warning(f"HTTP {e.code} em {request.path}: {e.description}")
            return e

        app.logger.exception("Erro não tratado:")
        return render_template("errors/500.html"), 500

    return app