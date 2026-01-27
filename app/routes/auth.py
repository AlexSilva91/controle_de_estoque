from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from app.services.crud import (
    abrir_caixa, 
    get_caixa_aberto, 
    get_user_by_cpf, 
    verify_password,
)
from app.database import SessionLocal
from app.models.entities import Caixa, StatusCaixa, Usuario
from zoneinfo import ZoneInfo 
from datetime import datetime
from app import schemas
from app.models import db
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/')
logger = logging.getLogger(__name__)

def get_session():
    """Obtém uma nova sessão do banco"""
    return SessionLocal()

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Usar uma nova sessão para cada requisição
        db = get_session()
        
        try:
            cpf = request.form.get('cpf', '').strip().replace('.', '').replace('-', '')
            senha = request.form.get('senha', '').strip()

            if not cpf or not senha:
                logger.warning("CPF ou senha não fornecidos")
                return jsonify({
                    'success': False,
                    'message': 'Preencha CPF e senha corretamente.'
                })

            usuario = get_user_by_cpf(db, cpf)
            if not usuario:
                logger.warning(f"Usuário não encontrado para CPF: {cpf}")
                return jsonify({
                    'success': False,
                    'message': 'Usuário não encontrado.'
                })

            if not verify_password(senha, usuario.senha_hash):
                logger.warning(f"Senha incorreta para CPF: {cpf}")
                return jsonify({
                    'success': False,
                    'message': 'Senha incorreta.'
                })

            if not usuario.status:
                logger.warning(f"Usuário inativo. Contate o administrador. CPF: {cpf}")
                return jsonify({
                    'success': False,
                    'message': 'Usuário inativo. Contate o administrador.'
                })

            login_user(usuario)
            
            # Verificar se é o primeiro login do usuário
            primeiro_login = usuario.ultimo_acesso is None
            
            # Atualiza último acesso
            usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
            db.commit()

            # Verificar caixa aberto apenas para operadores
            if usuario.tipo.value == 'operador':
                logger.info(f"Verificando caixa para operador {usuario.nome}")
                caixa_aberto = get_caixa_aberto(db, operador_id=usuario.id)
                
                if not caixa_aberto:
                    # Se é o primeiro login, mostra modal de abertura manual
                    if primeiro_login:
                        # Busca último caixa fechado para valor sugerido
                        ultimo_caixa = db.query(Caixa).filter(
                            Caixa.operador_id == usuario.id,
                            Caixa.status == StatusCaixa.fechado,
                            Caixa.valor_fechamento.isnot(None)
                        ).order_by(desc(Caixa.data_fechamento)).first()
                        
                        valor_sugerido = float(ultimo_caixa.valor_fechamento) if ultimo_caixa else 0.0
                        
                        return jsonify({
                            'success': True,
                            'needs_caixa': True,
                            'primeiro_login': True,
                            'valor_sugerido': valor_sugerido,
                            'user_type': 'operador'
                        })
                    else:
                        # Se não é o primeiro login, abre automaticamente com valor do último caixa
                        ultimo_caixa = db.query(Caixa).filter(
                            Caixa.operador_id == usuario.id,
                            Caixa.status == StatusCaixa.fechado,
                            Caixa.valor_fechamento.isnot(None)
                        ).order_by(desc(Caixa.data_fechamento)).first()
                        
                        # Define valor de abertura
                        if ultimo_caixa and ultimo_caixa.valor_fechamento:
                            valor_abertura = ultimo_caixa.valor_fechamento
                        else:
                            valor_abertura = Decimal('0.00')
                        
                        try:
                            # Abre o caixa automaticamente
                            novo_caixa = abrir_caixa(
                                db=db,
                                operador_id=usuario.id,
                                valor_abertura=valor_abertura,
                                observacao=f"Abertura automática - valor do último fechamento (Caixa #{ultimo_caixa.id})" if ultimo_caixa else "Abertura automática - primeiro caixa"
                            )
                            
                            if novo_caixa:
                                return jsonify({
                                    'success': True,
                                    'needs_caixa': False,
                                    'abertura_automatica': True,
                                    'caixa_id': novo_caixa.id,
                                    'valor_abertura': float(valor_abertura),
                                    'user_type': 'operador',
                                    'message': f'Caixa #{novo_caixa.id} aberto automaticamente com R$ {valor_abertura:.2f}'
                                })
                            else:
                                logger.error("Falha ao criar o caixa automaticamente")
                                raise Exception("Falha ao criar o caixa")
                                
                        except Exception as e:
                            db.rollback()
                            logger.error(f"Erro na abertura automática: {str(e)}")
                            # Se falhar na abertura automática, solicita abertura manual
                            return jsonify({
                                'success': True,
                                'needs_caixa': True,
                                'primeiro_login': False,
                                'erro_abertura_automatica': True,
                                'valor_sugerido': float(valor_abertura),
                                'user_type': 'operador',
                                'message': f'Erro na abertura automática: {str(e)}. Por favor, abra manualmente.'
                            })
                else:
                    logger.info(f"Usuário {usuario.id} já tem caixa aberto #{caixa_aberto.id}")

            return jsonify({
                'success': True,
                'needs_caixa': False,
                'user_type': usuario.tipo.value,
                'message': f'Bem-vindo, {usuario.nome}!'
            })
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro SQL: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Erro ao atualizar dados de acesso.'
            }), 500
        except Exception as e:
            db.rollback()
            logger.error(f"Erro geral no login: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }), 500
        finally:
            db.close()

    return render_template('login.html')

@auth_bp.route('/abrir-caixa', methods=['POST'])
@login_required
def abrir_caixa_manual():
    if current_user.tipo.value != 'operador':
        logger.warning(f"Tentativa de abertura de caixa por usuário não operador: {current_user.id}")
        return jsonify({
            'success': False,
            'message': 'Apenas operadores podem abrir caixa'
        }), 403

    # Usar uma nova sessão
    db = get_session()
    
    try:
        if not request.is_json:
            logger.warning("Content-Type inválido na abertura de caixa manual")
            return jsonify({'success': False, 'message': 'Content-Type deve ser application/json'}), 400

        data = request.get_json()
        if not data:
            logger.warning("Dados inválidos na abertura de caixa manual")
            return jsonify({'success': False, 'message': 'Dados inválidos'}), 400

        try:
            valor_abertura = Decimal(str(data.get('valor_abertura', 0)))
        except (ValueError, TypeError) as e:
            logger.warning(f"Valor de abertura inválido: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Valor de abertura inválido: {str(e)}'
            }), 400

        observacao = data.get('observacao', 'Abertura manual')

        # Verifica se já existe caixa aberto para o usuário atual
        caixa_existente = get_caixa_aberto(db, operador_id=current_user.id)
        if caixa_existente:
            logger.warning(f"Usuário {current_user.id} já tem caixa aberto #{caixa_existente.id}")
            return jsonify({
                'success': False,
                'message': f'Você já tem um caixa aberto (Caixa #{caixa_existente.id} aberto em {caixa_existente.data_abertura.strftime("%d/%m/%Y %H:%M")})',
                'caixa_id': caixa_existente.id,
                'redirect_url': url_for('operador.dashboard')
            }), 400

        # Tenta abrir o caixa
        novo_caixa = abrir_caixa(
            db=db,
            operador_id=current_user.id,
            valor_abertura=valor_abertura,
            observacao=observacao
        )
        
        if not novo_caixa:
            logger.error("Falha ao criar o caixa manualmente")
            raise ValueError("Erro ao criar caixa")
        
        return jsonify({
            'success': True,
            'message': f'Caixa #{novo_caixa.id} aberto com R$ {valor_abertura:.2f}',
            'caixa_id': novo_caixa.id,
            'redirect_url': url_for('operador.dashboard')
        })

    except ValueError as e:
        logger.warning(f"Erro de valor na abertura manual: {str(e)}")
        db.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Erro na abertura manual: {str(e)}", exc_info=True)
        db.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao abrir caixa: {str(e)}'
        }), 500
    finally:
        db.close()

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        usuario = Usuario.query.get(current_user.id)
        if usuario:
            usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
            db.session.commit()
    except Exception as e:
        logger.exception("Erro ao atualizar último acesso no logout")
        db.session.rollback()
    finally:
        db.session.close()  # garante liberar a sessão
    
    logout_user()
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('auth.login'))
