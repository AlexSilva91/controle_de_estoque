# routes/__init__.py
from flask import Blueprint

from .auth import auth_bp
from .admin import admin_bp
from .operador import operador_bp

def init_app(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(operador_bp)
