from flask import Blueprint, render_template, request, jsonify, current_app as app
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from app import db
from app.models import entities
from app.schemas import (
    ClienteCreate,
    ClienteBase,
    MovimentacaoEstoqueCreate,
)
from app.crud import (
    TipoMovimentacao,
    get_produto,
    get_produtos,
    registrar_movimentacao,
    get_clientes,
    create_cliente,
    update_cliente,
    delete_cliente,
    create_nota_fiscal,
    get_lancamentos_financeiros,
)

operador_bp = Blueprint('operador', __name__, url_prefix='/operador')

@operador_bp.route('/dashboard')
@login_required
def dashboard_operador():
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
        'ativo': produto.ativo
    } for produto in produtos])

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
    """Endpoint para registrar vendas com validação robusta"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type deve ser application/json'}), 400

    data = request.get_json()
    app.logger.info(f"Dados recebidos: {data}")

    # Validação básica
    required_fields = ['cliente_id', 'forma_pagamento', 'itens']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo obrigatório faltando: {field}'}), 400

    # Validar forma de pagamento
    if data['forma_pagamento'] not in [fp.value for fp in entities.FormaPagamento]:
        return jsonify({'error': 'Forma de pagamento inválida'}), 400

    try:
        # Validar itens
        if not isinstance(data['itens'], list) or len(data['itens']) == 0:
            return jsonify({'error': 'A lista de itens não pode estar vazia'}), 400

        # Consolidar itens duplicados
        consolidated_items = {}
        for item in data['itens']:
            key = (item['produto_id'], item['valor_unitario'])
            if key in consolidated_items:
                consolidated_items[key]['quantidade'] += Decimal(str(item['quantidade']))
            else:
                consolidated_items[key] = {
                    'produto_id': item['produto_id'],
                    'quantidade': Decimal(str(item['quantidade'])),
                    'valor_unitario': Decimal(str(item['valor_unitario']))
                }
        data['itens'] = list(consolidated_items.values())

        validated_items = []
        valor_total = Decimal('0')

        for item in data['itens']:
            # Validar campos do item
            if not all(k in item for k in ['produto_id', 'quantidade', 'valor_unitario']):
                return jsonify({'error': 'Item incompleto na lista de itens'}), 400

            try:
                # Converter e validar valores
                quantidade = Decimal(str(item['quantidade']))
                valor_unitario = Decimal(str(item['valor_unitario']))

                if quantidade <= 0:
                    return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
                if valor_unitario <= 0:
                    return jsonify({'error': 'Valor unitário deve ser maior que zero'}), 400

                # Verificar estoque
                produto = get_produto(db.session, item['produto_id'])
                if not produto:
                    return jsonify({'error': f'Produto ID {item["produto_id"]} não encontrado'}), 400

                if produto.estoque_quantidade < quantidade:
                    return jsonify({'error': f'Estoque insuficiente para o produto {produto.nome}'}), 400

                valor_item = quantidade * valor_unitario
                valor_total += valor_item

                validated_items.append({
                    'produto_id': int(item['produto_id']),
                    'quantidade': float(quantidade),
                    'valor_unitario': float(valor_unitario)
                })
            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Valores inválidos nos itens: {str(e)}'}), 400

        # Criar nota fiscal (sem chave_acesso pois é opcional)
        nota_data = {
            'cliente_id': int(data['cliente_id']),
            'valor_total': float(valor_total),
            'status': 'emitida',
            'observacao': data.get('observacao', ''),
            'itens': [{
                'produto_id': item['produto_id'],
                'quantidade': item['quantidade'],
                'valor_unitario': item['valor_unitario'],
                'valor_total': item['quantidade'] * item['valor_unitario']
            } for item in validated_items],
            'forma_pagamento': data['forma_pagamento']
        }

        print(f"Dados da nota fiscal: {nota_data}")

        db_nota = create_nota_fiscal(db.session, nota_data)
        print(f"Nota fiscal criada: {db_nota.id}\nUSUÁRIO: {current_user.id}, {current_user.nome}")

        # Registrar movimentação de estoque para cada item, convertendo dict para schema
        for item in validated_items:
            mov_data = MovimentacaoEstoqueCreate(
                produto_id=item['produto_id'],
                usuario_id=current_user.id,
                cliente_id=data['cliente_id'],
                tipo=TipoMovimentacao.saida,  # Enum para tipo 'saida'
                quantidade=Decimal(str(item['quantidade'])),
                valor_unitario=Decimal(str(item['valor_unitario'])),
                forma_pagamento=data['forma_pagamento'],
                observacao=data.get('observacao', '')
            )
            registrar_movimentacao(db.session, mov_data)

        return jsonify({
            'success': True,
            'nota_id': db_nota.id,
            'valor_total': float(valor_total)
        }), 201

    except ValueError as e:
        db.session.rollback()
        app.logger.error(f"Erro de validação: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Erro de banco de dados: {str(e)}")
        return jsonify({'error': 'Erro de banco de dados ao processar a venda'}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao processar a venda'}), 500
    
# ===== API SALDO =====
@operador_bp.route('/api/saldo', methods=['GET'])
@login_required
def api_get_saldo():
    lancamentos = get_lancamentos_financeiros(db.session)
    saldo = Decimal('0')

    for lanc in lancamentos:
        if lanc.tipo == 'entrada':
            saldo += Decimal(str(lanc.valor))
        else:
            saldo -= Decimal(str(lanc.valor))

    # Formata como string com 2 casas decimais e vírgula decimal:
    saldo_formatado = f"{saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    return jsonify({'saldo': str(saldo), 'saldo_formatado': saldo_formatado})

# ===== API FECHAMENTO DE CAIXA =====
@operador_bp.route('/api/fechar-caixa', methods=['POST'])
@login_required
def api_fechar_caixa():
    try:
        return jsonify({
            'success': True,
            'message': 'Caixa fechado com sucesso',
            'hora_fechamento': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
