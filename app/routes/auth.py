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
            # Atualiza último acesso
            usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
            db.commit()

            # Verificar caixa aberto apenas para operadores
            if usuario.tipo.value == 'operador':
                # CORREÇÃO: Passa o ID do usuário específico para verificar apenas seus caixas
                caixa_aberto = get_caixa_aberto(db, operador_id=usuario.id)
                
                if not caixa_aberto:
                    # Se não tem caixa aberto, verifica último fechado para sugerir valor
                    ultimo_caixa = get_ultimo_caixa_fechado(db, operador_id=usuario.id)
                    valor_sugerido = float(ultimo_caixa.valor_fechamento) if ultimo_caixa else 0.0
                    
                    return jsonify({
                        'success': True,
                        'needs_caixa': True,
                        'valor_sugerido': valor_sugerido,
                        'user_type': 'operador'
                    })
                else:
                    # Se já tem caixa aberto, registra no log e segue normalmente
                    print(f"Usuário {usuario.id} já tem caixa aberto #{caixa_aberto.id}")

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
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type deve ser application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dados inválidos'}), 400

        try:
            valor_abertura = Decimal(str(data.get('valor_abertura', 0)))
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Valor de abertura inválido'
            }), 400

        observacao = data.get('observacao', 'Abertura manual')

        # CORREÇÃO: Verifica apenas caixas do usuário atual
        caixa_existente = get_caixa_aberto(db, operador_id=current_user.id)
        if caixa_existente:
            return jsonify({
                'success': False,
                'message': f'Você já tem um caixa aberto (Caixa #{caixa_existente.id} aberto em {caixa_existente.data_abertura.strftime("%d/%m/%Y %H:%M")})',
                'caixa_id': caixa_existente.id,
                'redirect_url': url_for('operador.dashboard')
            }), 400

        # Tenta abrir o caixa (a função já faz a verificação internamente)
        novo_caixa = abrir_caixa(
            db=db,
            operador_id=current_user.id,
            valor_abertura=valor_abertura,
            observacao=observacao
        )
        
        if not novo_caixa:
            raise ValueError("Erro ao criar caixa")
        
        return jsonify({
            'success': True,
            'message': f'Caixa #{novo_caixa.id} aberto com R$ {valor_abertura:.2f}',
            'caixa_id': novo_caixa.id,
            'redirect_url': url_for('operador.dashboard')
        })

    except ValueError as e:
        db.rollback()
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