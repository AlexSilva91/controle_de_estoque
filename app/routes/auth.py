from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from app.crud import (
    abrir_caixa, 
    get_caixa_aberto, 
    get_user_by_cpf, 
    verify_password,
)
from app.database import SessionLocal
from app.models.entities import Caixa, StatusCaixa, Usuario, AuditLog
from zoneinfo import ZoneInfo 
from datetime import datetime
from app import schemas
from app.models import db
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/')
logger = logging.getLogger(__name__)

def get_session():
    return SessionLocal()

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_session()
        
        try:
            cpf = request.form.get('cpf', '').strip().replace('.', '').replace('-', '')
            senha = request.form.get('senha', '').strip()

            if not cpf or not senha:
                return jsonify({'success': False,'message': 'Preencha CPF e senha corretamente.'})

            usuario = get_user_by_cpf(db, cpf)
            if not usuario:
                return jsonify({'success': False,'message': 'Usuário não encontrado.'})

            if not verify_password(senha, usuario.senha_hash):
                return jsonify({'success': False,'message': 'Senha incorreta.'})

            if not usuario.status:
                return jsonify({'success': False,'message': 'Usuário inativo. Contate o administrador.'})

            login_user(usuario)
            
            primeiro_login = usuario.ultimo_acesso is None
            antes = f"Último acesso: {usuario.ultimo_acesso}"
            usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
            db.commit()

            AuditLog.registrar(
                session=db,
                tabela="usuarios",
                registro_id=usuario.id,
                acao="atualizar_ultimo_acesso",
                usuario_id=usuario.id,
                antes=antes,
                depois=f"Login: {usuario.ultimo_acesso}"
            )

            if usuario.tipo.value == 'operador':
                caixa_aberto = get_caixa_aberto(db, operador_id=usuario.id)
                
                if not caixa_aberto:
                    if primeiro_login:
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
                        ultimo_caixa = db.query(Caixa).filter(
                            Caixa.operador_id == usuario.id,
                            Caixa.status == StatusCaixa.fechado,
                            Caixa.valor_fechamento.isnot(None)
                        ).order_by(desc(Caixa.data_fechamento)).first()
                        
                        if ultimo_caixa:
                            valor_abertura = ultimo_caixa.valor_fechamento
                        else:
                            valor_abertura = Decimal('0.00')
                        
                        try:
                            novo_caixa = abrir_caixa(
                                db=db,
                                operador_id=usuario.id,
                                valor_abertura=valor_abertura,
                                observacao=f"Abertura automática - valor do último fechamento (Caixa #{ultimo_caixa.id})" if ultimo_caixa else "Abertura automática - primeiro caixa"
                            )

                            AuditLog.registrar(
                                session=db,
                                tabela="caixas",
                                registro_id=novo_caixa.id,
                                acao="abertura_automatica",
                                usuario_id=usuario.id,
                                antes="Sem caixa aberto",
                                depois=f"Caixa aberto automaticamente com valor {valor_abertura}"
                            )
                            
                            return jsonify({
                                'success': True,
                                'needs_caixa': False,
                                'abertura_automatica': True,
                                'caixa_id': novo_caixa.id,
                                'valor_abertura': float(valor_abertura),
                                'user_type': 'operador',
                                'message': f'Caixa #{novo_caixa.id} aberto automaticamente com R$ {valor_abertura:.2f}'
                            })
                                
                        except Exception as e:
                            db.rollback()
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
                    pass

            return jsonify({
                'success': True,
                'needs_caixa': False,
                'user_type': usuario.tipo.value,
                'message': f'Bem-vindo, {usuario.nome}!'
            })
            
        except SQLAlchemyError:
            db.rollback()
            return jsonify({'success': False,'message': 'Erro ao atualizar dados de acesso.'}), 500
        except Exception as e:
            db.rollback()
            return jsonify({'success': False,'message': f'Erro interno: {str(e)}'}), 500
        finally:
            db.close()

    return render_template('login.html')

@auth_bp.route('/abrir-caixa', methods=['POST'])
@login_required
def abrir_caixa_manual():
    if current_user.tipo.value != 'operador':
        return jsonify({'success': False,'message': 'Apenas operadores podem abrir caixa'}), 403

    db = get_session()
    
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type deve ser application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False,'message': 'Dados inválidos'}), 400

        try:
            valor_abertura = Decimal(str(data.get('valor_abertura', 0)))
        except:
            return jsonify({'success': False,'message': 'Valor de abertura inválido'}), 400

        observacao = data.get('observacao', 'Abertura manual')

        caixa_existente = get_caixa_aberto(db, operador_id=current_user.id)
        if caixa_existente:
            return jsonify({
                'success': False,
                'message': f'Você já tem um caixa aberto (Caixa #{caixa_existente.id} aberto em {caixa_existente.data_abertura.strftime("%d/%m/%Y %H:%M")})',
                'caixa_id': caixa_existente.id,
                'redirect_url': url_for('operador.dashboard')
            }), 400

        novo_caixa = abrir_caixa(
            db=db,
            operador_id=current_user.id,
            valor_abertura=valor_abertura,
            observacao=observacao
        )
        
        if not novo_caixa:
            raise ValueError("Erro ao criar caixa")

        AuditLog.registrar(
            session=db,
            tabela="caixas",
            registro_id=novo_caixa.id,
            acao="abertura_manual",
            usuario_id=current_user.id,
            antes="Sem caixa aberto",
            depois=f"Caixa aberto manualmente com valor {valor_abertura}"
        )
        
        return jsonify({
            'success': True,
            'message': f'Caixa #{novo_caixa.id} aberto com R$ {valor_abertura:.2f}',
            'caixa_id': novo_caixa.id,
            'redirect_url': url_for('operador.dashboard')
        })

    except Exception as e:
        db.rollback()
        return jsonify({'success': False,'message': f'Erro ao abrir caixa: {str(e)}'}), 500
    finally:
        db.close()

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        usuario = Usuario.query.get(current_user.id)
        if usuario:
            antes = f"Último acesso: {usuario.ultimo_acesso}"
            usuario.ultimo_acesso = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
            db.session.commit()

            AuditLog.registrar(
                session=db.session,
                tabela="usuarios",
                registro_id=current_user.id,
                acao="logout",
                usuario_id=current_user.id,
                antes=antes,
                depois=f"Logout realizado em {usuario.ultimo_acesso}"
            )
    except:
        db.session.rollback()
    finally:
        db.session.close()
    
    logout_user()
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('auth.login'))
