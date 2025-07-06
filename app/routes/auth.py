from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.crud import get_user_by_cpf, verify_password
from app.database import SessionLocal

auth_bp = Blueprint('auth', __name__, url_prefix='/')
db = SessionLocal()

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip().replace('.', '').replace('-', '')
        senha = request.form.get('senha', '').strip()

        if not cpf or not senha:
            flash('Preencha CPF e senha corretamente.', 'danger')
            return render_template('login.html')

        usuario = get_user_by_cpf(db, cpf)
        if not usuario:
            flash('Usuário não encontrado.', 'danger')
            return render_template('login.html')

        if not verify_password(senha, usuario.senha_hash):
            flash('Senha incorreta.', 'danger')
            return render_template('login.html')

        # Faz login com Flask-Login
        login_user(usuario)

        flash(f'Bem-vindo, {usuario.nome}!', 'success')

        if usuario.tipo.value == 'admin':
            return redirect(url_for('admin.dashboard_admin'))
        elif usuario.tipo.value == 'operador':
            return redirect(url_for('operador.dashboard_operador'))
        else:
            flash('Tipo de usuário inválido.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('auth.login'))
