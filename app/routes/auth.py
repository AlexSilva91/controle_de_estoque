from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.crud import abrir_caixa, get_caixa_aberto, get_ultimo_caixa_fechado, get_user_by_cpf, verify_password
from app.database import SessionLocal
from zoneinfo import ZoneInfo 
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/')
db = SessionLocal()

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip().replace('.', '').replace('-', '')
        senha = request.form.get('senha', '').strip()

        if not cpf or not senha:
            return jsonify({
                'success': False,
                'message': 'Preencha CPF e senha corretamente.'
            })

        usuario = get_user_by_cpf(db, cpf)
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado.'
            })

        if not verify_password(senha, usuario.senha_hash):
            return jsonify({
                'success': False,
                'message': 'Senha incorreta.'
            })

        if not usuario.status:
            return jsonify({
                'success': False,
                'message': 'Usuário inativo. Contate o administrador.'
            })

        login_user(usuario)
        usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
        db.commit()

        # Verificar caixa aberto para operadores
        if usuario.tipo.value == 'operador':
            caixa_aberto = get_caixa_aberto(db)
            if not caixa_aberto:
                ultimo_caixa = get_ultimo_caixa_fechado(db)
                valor_sugerido = float(ultimo_caixa.valor_fechamento) if ultimo_caixa else 0.0
                
                return jsonify({
                    'success': True,
                    'needs_caixa': True,
                    'valor_sugerido': valor_sugerido,
                    'user_type': 'operador'
                })

        return jsonify({
            'success': True,
            'needs_caixa': False,
            'user_type': usuario.tipo.value,
            'message': f'Bem-vindo, {usuario.nome}!'
        })

    return render_template('login.html')

@auth_bp.route('/abrir-caixa', methods=['POST'])
@login_required
def abrir_caixa_manual():
    if current_user.tipo.value != 'operador':
        return jsonify({
            'success': False,
            'message': 'Apenas operadores podem abrir caixa'
        }), 403

    try:
        data = request.get_json()
        valor_abertura = Decimal(str(data.get('valor_abertura', 0)))
        observacao = data.get('observacao', 'Abertura manual')

        novo_caixa = abrir_caixa(
            db,
            current_user.id,
            valor_abertura,
            observacao
        )
        
        return jsonify({
            'success': True,
            'message': f'Caixa aberto com R$ {valor_abertura:.2f}',
            'caixa_id': novo_caixa.id,
            'redirect_url': url_for('operador.dashboard')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao abrir caixa: {str(e)}'
        }), 500

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('auth.login'))