from flask import redirect, url_for, render_template
from flask_login import current_user
from flask import Blueprint

home = Blueprint('home', __name__, url_prefix='/home')

@home.route('/')
def home_index():
    if current_user.is_authenticated:
        # pega o valor real do Enum
        tipo = current_user.tipo.value  
        if tipo == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif tipo == 'operador':
            return redirect(url_for('operador.dashboard'))
        else:
            return redirect(url_for('auth.login'))
        
    return redirect(url_for('auth.login'))