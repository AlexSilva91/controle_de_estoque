from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.crud import abrir_caixa, get_caixa_aberto, get_ultimo_caixa_fechado, get_user_by_cpf, verify_password
from app.database import SessionLocal
from zoneinfo import ZoneInfo 

auth_bp = Blueprint('auth', __name__, url_prefix='/')
db = SessionLocal()

from datetime import datetime

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

        if not usuario.status:
            flash('Usuário inativo. Contate o administrador.', 'danger')
            return render_template('login.html')

        login_user(usuario)


        usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
        db.commit()

        # Lógica de abertura de caixa para operadores
        if usuario.tipo.value == 'operador':
            caixa_aberto = get_caixa_aberto(db)
            if not caixa_aberto:
                ultimo_caixa = get_ultimo_caixa_fechado(db)
                valor_abertura = ultimo_caixa.valor_fechamento if ultimo_caixa else Decimal('00.00')
                
                try:
                    novo_caixa = abrir_caixa(
                        db,
                        usuario.id,
                        valor_abertura,
                        "Abertura automática ao login"
                    )
                    flash(f'Caixa aberto automaticamente com R$ {valor_abertura:.2f}', 'success')
                except Exception as e:
                    flash(f'Erro ao abrir caixa: {str(e)}', 'danger')
                    return render_template('login.html')

        flash(f'Bem-vindo, {usuario.nome}!', 'success')

        if usuario.tipo.value == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif usuario.tipo.value == 'operador':
            return redirect(url_for('operador.dashboard'))
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
