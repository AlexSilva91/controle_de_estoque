from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app.crud import (
    abrir_caixa, 
    get_caixa_aberto, 
    get_ultimo_caixa_fechado, 
    get_user_by_cpf, 
    verify_password,
    get_user_by_id,
    update_user
)
from app.database import SessionLocal
from zoneinfo import ZoneInfo 
from datetime import datetime
from app import schemas

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
        
        try:
            # Atualiza último acesso diretamente no objeto
            usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
            db.commit()

            # Verificar caixa aberto para operadores
            if usuario.tipo.value == 'operador':
                caixa_aberto = get_caixa_aberto(db)
                if not caixa_aberto:
                    ultimo_caixa = get_ultimo_caixa_fechado(db)
                    # Verifica se ultimo_caixa existe e tem o atributo valor_fechamento
                    valor_sugerido = float(ultimo_caixa.valor_fechamento) if ultimo_caixa and hasattr(ultimo_caixa, 'valor_fechamento') else 0.0
                    
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
            
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao atualizar dados de acesso.'
            }), 500

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
        if not data:
            return jsonify({'success': False, 'message': 'Dados inválidos'}), 400

        # Verifica e converte o valor de abertura
        try:
            valor_abertura = Decimal(str(data.get('valor_abertura', 0)))
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Valor de abertura inválido'
            }), 400

        observacao = data.get('observacao', 'Abertura manual')

        # Tenta abrir o caixa
        novo_caixa = abrir_caixa(
            db=db,
            operador_id=current_user.id,
            valor_abertura=valor_abertura,
            observacao=observacao
        )
        
        # Verifica se o caixa foi criado corretamente
        if not novo_caixa or not hasattr(novo_caixa, 'id'):
            raise ValueError("Erro ao criar caixa")
        
        return jsonify({
            'success': True,
            'message': f'Caixa aberto com R$ {valor_abertura:.2f}',
            'caixa_id': novo_caixa.id,
            'redirect_url': url_for('operador.dashboard')
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao abrir caixa: {str(e)}'
        }), 500

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        # Atualiza último acesso antes de fazer logout
        current_user.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
    
    logout_user()
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('auth.login'))