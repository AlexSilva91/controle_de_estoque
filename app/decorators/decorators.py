from functools import wraps
from flask_login import current_user
from flask import jsonify

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "message": "Acesso não autorizado"}), 401
        if (current_user.tipo != "admin"): 
            return (jsonify({"success": False, "message": "Acesso restrito a administradores"}),403,)
        return f(*args, **kwargs)

    return decorated_function

def operador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "message": "Acesso não autorizado"}), 401
        if (current_user.tipo != "operador"):
            return (jsonify({"success": False, "message": "Acesso restrito a operadores"}),403,)
        return f(*args, **kwargs)

    return decorated_function