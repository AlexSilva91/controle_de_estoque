# routes/__init__.py
from flask import Blueprint

from .home import home
from .auth import auth_bp
from .admin import admin_bp
from .operador import operador_bp
from .admin_fiscal import fiscal_bp

def init_app(app):
    app.register_blueprint(home)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(operador_bp)
    app.register_blueprint(fiscal_bp)