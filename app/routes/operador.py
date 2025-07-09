from flask import Blueprint, render_template, request, jsonify, current_app as app
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from app import db
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.models import entities
from app.schemas import (
    ClienteCreate,
    ClienteBase,
    MovimentacaoEstoqueCreate,
)
from app.crud import (
    CategoriaFinanceira,
    StatusCaixa,
    TipoMovimentacao,
    create_lancamento_financeiro,
    get_produto,
    get_produtos,
    get_ultimo_caixa_fechado,
    registrar_movimentacao,
    get_clientes,
    create_cliente,
    update_cliente,
    delete_cliente,
    create_nota_fiscal,
    get_lancamentos_financeiros,
    get_caixa_aberto,
    fechar_caixa,
    abrir_caixa,
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
    } for produto in produtos if produto.estoque_quantidade >= 1])

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
    required_fields = ['cliente_id', 'forma_pagamento', 'itens', 'valor_recebido']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo obrigatório faltando: {field}'}), 400

    # Validar forma de pagamento
    if data['forma_pagamento'] not in [fp.value for fp in entities.FormaPagamento]:
        return jsonify({'error': 'Forma de pagamento inválida'}), 400

    try:
        # Verificar caixa aberto
        caixa = get_caixa_aberto(db.session)
        if not caixa:
            return jsonify({'error': 'Nenhum caixa aberto encontrado'}), 400

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
                    'valor_unitario': float(valor_unitario),
                    'valor_total': float(valor_item)
                })
            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Valores inválidos nos itens: {str(e)}'}), 400

        # Validar valor recebido
        valor_recebido = Decimal(str(data['valor_recebido']))
        if valor_recebido < valor_total and data['forma_pagamento'] != 'a_prazo':
            return jsonify({'error': 'Valor recebido menor que o valor total'}), 400

        # Calcular troco
        troco = valor_recebido - valor_total if valor_recebido > valor_total else Decimal('0')

        # Criar nota fiscal
        nota_data = {
            'cliente_id': int(data['cliente_id']),
            'valor_total': float(valor_total),
            'status': 'emitida',
            'observacao': data.get('observacao', ''),
            'itens': validated_items,
            'forma_pagamento': data['forma_pagamento'],
            'valor_recebido': float(valor_recebido),
            'troco': float(troco),
            'caixa_id': caixa.id
        }

        db_nota = create_nota_fiscal(db.session, nota_data)

        # Registrar movimentação de estoque para cada item
        for item in validated_items:
            mov_data = MovimentacaoEstoqueCreate(
                produto_id=item['produto_id'],
                usuario_id=current_user.id,
                cliente_id=data['cliente_id'],
                caixa_id=caixa.id,
                tipo=TipoMovimentacao.saida,
                quantidade=Decimal(str(item['quantidade'])),
                valor_unitario=Decimal(str(item['valor_unitario'])),
                forma_pagamento=data['forma_pagamento'],
                valor_recebido=valor_recebido,
                troco=troco,
                observacao=data.get('observacao', '')
            )
            registrar_movimentacao(db.session, mov_data)

        return jsonify({
            'success': True,
            'nota_id': db_nota.id,
            'valor_total': float(valor_total),
            'troco': float(troco)
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
    try:
        caixa = get_caixa_aberto(db.session)

        if not caixa:
            ultimo_caixa = get_ultimo_caixa_fechado(db.session)
            if ultimo_caixa:
                return jsonify({
                    'saldo': str(ultimo_caixa.valor_fechamento),
                    'saldo_formatado': f"R$ {ultimo_caixa.valor_fechamento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'caixa_id': None,
                    'valor_abertura': 0.00,
                    'message': 'Nenhum caixa aberto encontrado (último fechamento)'
                })
            return jsonify({
                'saldo': '0.00',
                'saldo_formatado': 'R$ 0,00',
                'caixa_id': None,
                'valor_abertura': 0.00,
                'message': 'Nenhum caixa aberto encontrado'
            })

        # Define início e fim do dia de hoje
        inicio_hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fim_hoje = inicio_hoje + timedelta(days=1)

        # Busca lançamentos apenas do dia atual
        lancamentos = db.session.query(entities.Financeiro).filter(
            entities.Financeiro.data >= inicio_hoje,
            entities.Financeiro.data < fim_hoje
        ).all()

        saldo = Decimal("0.00")

        for lanc in lancamentos:
            if lanc.tipo == 'entrada' and lanc.categoria not in [CategoriaFinanceira.fechamento_caixa, CategoriaFinanceira.abertura_caixa]:
                saldo += Decimal(str(lanc.valor))

        saldo_formatado = f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"Saldo calculado: {saldo}, Formato: {saldo_formatado}")

        return jsonify({
            'saldo': str(saldo),
            'saldo_formatado': saldo_formatado,
            'caixa_id': caixa.id,
            'valor_abertura': float(caixa.valor_abertura),
            'message': 'Saldo atualizado com sucesso'
        })

    except Exception as e:
        app.logger.error(f"Erro ao calcular saldo: {str(e)}")
        return jsonify({
            'error': 'Erro ao calcular saldo',
            'details': str(e)
        }), 500

# ===== API ABERTURA DE CAIXA =====
@operador_bp.route('/api/abrir-caixa', methods=['POST'])
@login_required
def api_abrir_caixa():
    try:
        data = request.get_json()
        valor_abertura = Decimal(str(data.get('valor_abertura', 0)))
        
        if valor_abertura <= 0:
            return jsonify({'error': 'Valor de abertura deve ser maior que zero'}), 400
        
        caixa = abrir_caixa(
            db.session,
            current_user.id,
            valor_abertura,
            data.get('observacao', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'Caixa aberto com sucesso',
            'caixa_id': caixa.id,
            'valor_abertura': float(caixa.valor_abertura),
            'data_abertura': caixa.data_abertura.isoformat()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API FECHAMENTO DE CAIXA =====
@operador_bp.route('/api/fechar-caixa', methods=['POST'])
@login_required
def api_fechar_caixa():
    try:
        data = request.get_json()

        operador_id = current_user.id
        valor_fechamento = Decimal(str(data.get("valor_fechamento")))
        observacao = data.get("observacao", "")

        caixa_fechado = fechar_caixa(db.session, operador_id, valor_fechamento, observacao)

        return jsonify({
            "message": "Caixa fechado com sucesso.",
            "caixa_id": caixa_fechado.id,
            "valor_fechamento": str(caixa_fechado.valor_fechamento)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400