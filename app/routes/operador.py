import threading
from flask import Blueprint, render_template, request, jsonify, current_app as app
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from app import db
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.bot.bot_movimentacao import enviar_resumo_movimentacao_diaria
from app.models import entities
from app.schemas import (
    ClienteCreate,
    ClienteBase,
    MovimentacaoEstoqueCreate,
)
from app.crud import (
    StatusCaixa,
    registrar_venda_completa,
    get_caixa_aberto,
    get_clientes,
    get_produtos,
    get_produto,
    abrir_caixa,
    fechar_caixa,
    get_lancamentos_financeiros,
    get_ultimo_caixa_fechado,
    create_cliente,
    update_cliente,
    delete_cliente
)

operador_bp = Blueprint('operador', __name__, url_prefix='/operador')

@operador_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard_operador.html', nome_usuario=current_user.nome)

# ===== API CLIENTES =====
@operador_bp.route('/api/clientes', methods=['GET'])
@login_required
def api_get_clientes():
    clientes = get_clientes(db.session)
    return jsonify([{
        'id': cliente.id,
        'nome': cliente.nome,
        'documento': cliente.documento,
        'telefone': cliente.telefone,
        'email': cliente.email,
        'endereco': cliente.endereco,
        'ativo': cliente.ativo
    } for cliente in clientes])

@operador_bp.route('/api/clientes', methods=['POST'])
@login_required
def api_create_cliente():
    data = request.get_json()
    try:
        cliente = ClienteCreate(**data)
        cliente.ativo = True
        db_cliente = create_cliente(db.session, cliente)
        return jsonify({
            'id': db_cliente.id,
            'nome': db_cliente.nome,
            'documento': db_cliente.documento,
            'telefone': db_cliente.telefone,
            'email': db_cliente.email,
            'endereco': db_cliente.endereco
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@operador_bp.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
@login_required
def api_update_cliente(cliente_id):
    data = request.get_json()
    try:
        cliente_data = ClienteBase(**data)
        db_cliente = update_cliente(db.session, cliente_id, cliente_data)
        return jsonify({
            'id': db_cliente.id,
            'nome': db_cliente.nome,
            'documento': db_cliente.documento,
            'telefone': db_cliente.telefone,
            'email': db_cliente.email,
            'endereco': db_cliente.endereco
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@operador_bp.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required
def api_delete_cliente(cliente_id):
    try:
        success = delete_cliente(db.session, cliente_id)
        return jsonify({'success': success}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# ===== API PRODUTOS =====
@operador_bp.route('/api/produtos', methods=['GET'])
@login_required
def api_get_produtos():
    produtos = get_produtos(db.session)
    return jsonify([{
        'id': produto.id,
        'nome': produto.nome,
        'codigo': produto.codigo,
        'tipo': produto.tipo,
        'marca': produto.marca,
        'unidade': produto.unidade,
        'valor_unitario': float(produto.valor_unitario),
        'estoque_quantidade': float(produto.estoque_quantidade),
        'ativo': produto.ativo,
        'descricao': f"{produto.nome} ({produto.marca})" if produto.marca else produto.nome
    } for produto in produtos if produto.estoque_quantidade > 0])

@operador_bp.route('/api/produtos/<int:produto_id>', methods=['GET'])
@login_required
def api_get_produto(produto_id):
    produto = get_produto(db.session, produto_id)
    if produto:
        return jsonify({
            'id': produto.id,
            'nome': produto.nome,
            'codigo': produto.codigo,
            'tipo': produto.tipo,
            'marca': produto.marca,
            'unidade': produto.unidade,
            'valor_unitario': float(produto.valor_unitario),
            'estoque_quantidade': float(produto.estoque_quantidade),
            'ativo': produto.ativo
        })
    return jsonify({'error': 'Produto não encontrado'}), 404

# ===== API VENDAS =====
@operador_bp.route('/api/vendas', methods=['POST'])
@login_required
def api_registrar_venda():
    """Endpoint para registrar vendas"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 400

        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({'error': 'Dados JSON inválidos'}), 400

        app.logger.info(f"Dados recebidos: {data}")

        required_fields = ['cliente_id', 'forma_pagamento', 'itens']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório faltando: {field}'}), 400

        if not isinstance(data['itens'], list) or len(data['itens']) == 0:
            return jsonify({'error': 'Lista de itens inválida'}), 400

        for i, item in enumerate(data['itens']):
            if not isinstance(item, dict):
                return jsonify({'error': f'Item {i} não é um objeto válido'}), 400

            required_item_fields = ['produto_id', 'quantidade', 'valor_unitario']
            for field in required_item_fields:
                if field not in item:
                    return jsonify({'error': f'Item {i} está faltando o campo: {field}'}), 400

            try:
                item['quantidade'] = float(item['quantidade'])
                item['valor_unitario'] = float(item['valor_unitario'])
                if 'valor_total' in item:
                    item['valor_total'] = float(item['valor_total'])
                else:
                    item['valor_total'] = item['quantidade'] * item['valor_unitario']
            except (ValueError, TypeError):
                return jsonify({'error': f'Valores inválidos no item {i}'}), 400

        # Verifica se o operador possui um caixa aberto
        caixa = entities.Caixa.query.filter_by(operador_id=current_user.id, status=StatusCaixa.aberto).first()
        if not caixa:
            return jsonify({'error': 'Nenhum caixa aberto encontrado para este operador'}), 400

        # Processa a venda
        nota_id = registrar_venda_completa(db.session, data, operador_id=current_user.id, caixa_id=caixa.id)
        return jsonify({'mensagem': 'Venda registrada com sucesso', 'nota_id': nota_id}), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao registrar venda: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao processar a venda'}), 500

# ===== API SALDO =====
@operador_bp.route('/api/saldo', methods=['GET'])
@login_required
def api_get_saldo():
    try:
        caixa = get_caixa_aberto(db.session)
        
        if not caixa:
            ultimo_caixa = get_ultimo_caixa_fechado(db.session)
            if ultimo_caixa:
                return jsonify({
                    'saldo': float(ultimo_caixa.valor_fechamento),
                    'saldo_formatado': f"R$ {ultimo_caixa.valor_fechamento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'valor_abertura': 0.00,
                    'message': 'Nenhum caixa aberto encontrado'
                })
            return jsonify({
                'saldo': 0.00,
                'saldo_formatado': 'R$ 0,00',
                'valor_abertura': 0.00,
                'message': 'Nenhum caixa aberto encontrado'
            })

        # Calcula saldo baseado nas movimentações do dia
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        lancamentos = get_lancamentos_financeiros(
            db.session,
            data_inicio=datetime.combine(hoje, datetime.min.time()),
            data_fim=datetime.combine(hoje, datetime.max.time())
        )
        
        saldo = Decimal(str(caixa.valor_abertura))
        
        for lanc in lancamentos:
            if lanc.tipo == 'entrada' and lanc.categoria == 'venda':
                saldo += Decimal(str(lanc.valor))
        
        return jsonify({
            'saldo': float(saldo),
            'saldo_formatado': f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_abertura': float(caixa.valor_abertura),
            'message': 'Saldo atualizado com sucesso'
        })
    
    except Exception as e:
        app.logger.error(f"Erro ao calcular saldo: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ===== API ABERTURA DE CAIXA =====
@operador_bp.route('/api/abrir-caixa', methods=['POST'])
@login_required
def api_abrir_caixa():
    try:
        data = request.get_json()
        valor = Decimal(str(data.get('valor_abertura', 0)))
        
        if valor <= 0:
            return jsonify({'error': 'Valor de abertura inválido'}), 400
        
        caixa = abrir_caixa(
            db.session,
            current_user.id,
            valor,
            data.get('observacao', '')
        )
        
        return jsonify({
            'success': True,
            'caixa_id': caixa.id,
            'valor_abertura': float(valor)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ===== API FECHAMENTO DE CAIXA =====
@operador_bp.route('/api/fechar-caixa', methods=['POST'])
@login_required
def api_fechar_caixa():
    try:
        data = request.get_json()
        valor = Decimal(str(data.get('valor_fechamento', 0)))
        
        if valor <= 0:
            return jsonify({'error': 'Valor de fechamento inválido'}), 400
        
        caixa = fechar_caixa(
            db.session,
            current_user.id,
            valor,
            data.get('observacao', '')
        )
        
        # Envia relatório em segundo plano
        threading.Thread(target=enviar_resumo_movimentacao_diaria).start()
        
        return jsonify({
            'success': True,
            'caixa_id': caixa.id,
            'valor_fechamento': float(valor)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ===== API BUSCAS =====
@operador_bp.route('/api/clientes/buscar', methods=['GET'])
@login_required
def api_buscar_clientes():
    termo = request.args.get('q', '').lower()
    clientes = get_clientes(db.session)
    
    resultados = []
    for cliente in clientes:
        if (termo in cliente.nome.lower() or 
            (cliente.documento and termo in cliente.documento.lower()) or 
            (cliente.telefone and termo in cliente.telefone.lower())):
            
            resultados.append({
                'id': cliente.id,
                'nome': cliente.nome,
                'documento': cliente.documento,
                'telefone': cliente.telefone
            })
    
    return jsonify(resultados)

@operador_bp.route('/api/produtos/buscar', methods=['GET'])
@login_required
def api_buscar_produtos():
    termo = request.args.get('q', '').lower()
    produtos = get_produtos(db.session)
    
    resultados = []
    for produto in produtos:
        if (termo in produto.nome.lower() or 
            (produto.marca and termo in produto.marca.lower()) or 
            (produto.codigo and termo in produto.codigo.lower())):
            
            resultados.append({
                'id': produto.id,
                'nome': produto.nome,
                'marca': produto.marca,
                'valor_unitario': float(produto.valor_unitario),
                'estoque_quantidade': float(produto.estoque_quantidade),
                'descricao': f"{produto.nome} ({produto.marca})" if produto.marca else produto.nome
            })
    
    return jsonify(resultados)

@operador_bp.route('/api/usuario', methods=['GET'])
@login_required
def api_get_usuario():
    return jsonify({
        'id': current_user.id,
        'nome': current_user.nome,
        'tipo': current_user.tipo
    })