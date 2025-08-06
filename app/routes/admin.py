from functools import wraps
from zoneinfo import ZoneInfo
from flask import Blueprint, app, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import traceback

from sqlalchemy import func
from sqlalchemy.orm import Session
from app import schemas
from app.models import db
from app.models import entities
from app.crud import (
    TipoEstoque, atualizar_desconto, buscar_desconto_by_id, buscar_descontos_por_produto_id, buscar_todos_os_descontos, criar_desconto, deletar_desconto, get_caixa_aberto, abrir_caixa, fechar_caixa, get_caixas, get_caixa_by_id, get_transferencias,
    get_user_by_cpf, get_user_by_id, get_usuarios, create_user, obter_caixas_completo, registrar_transferencia, update_user,
    get_produto, get_produtos, create_produto, update_produto, delete_produto,
    registrar_movimentacao, get_cliente, get_clientes, create_cliente, 
    update_cliente, delete_cliente, create_nota_fiscal, get_nota_fiscal, 
    get_notas_fiscais, create_lancamento_financeiro, get_lancamento_financeiro,
    get_lancamentos_financeiros, update_lancamento_financeiro, 
    delete_lancamento_financeiro, get_clientes_all
)
from app.schemas import (
    UsuarioCreate, UsuarioUpdate, ProdutoCreate, ProdutoUpdate, MovimentacaoEstoqueCreate,
    ClienteCreate, ClienteUpdate, FinanceiroCreate, FinanceiroUpdate
)
from app.utils.format_data_moeda import formatar_data_br, formatar_valor_br

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
        if current_user.tipo != 'admin':  # Supondo que 'tipo' seja o campo que define o tipo de usuário
            return jsonify({'success': False, 'message': 'Acesso restrito a administradores'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ===== Dashboard Routes =====
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('dashboard_admin.html', nome_usuario=current_user.nome)

@admin_bp.route('/dashboard/metrics')
@login_required
@admin_required
def get_dashboard_metrics():
    try:
        # Caixa aberto
        caixa = get_caixa_aberto(db.session)
        
        # Contadores
        clientes_count = db.session.query(entities.Cliente).filter(entities.Cliente.ativo == True).count()
        produtos_count = db.session.query(entities.Produto).filter(entities.Produto.ativo == True).count()
        notas_count = db.session.query(entities.NotaFiscal).count()

        # Estoque por unidade de medida
        estoque_kg = db.session.query(
            func.sum(entities.Produto.estoque_loja)
        ).filter(
            entities.Produto.unidade == entities.UnidadeMedida.kg,
            entities.Produto.ativo == True
        ).scalar() or 0

        estoque_saco = db.session.query(
            func.sum(entities.Produto.estoque_loja)
        ).filter(
            entities.Produto.unidade == entities.UnidadeMedida.saco,
            entities.Produto.ativo == True
        ).scalar() or 0

        estoque_unidade = db.session.query(
            func.sum(entities.Produto.estoque_loja)
        ).filter(
            entities.Produto.unidade == entities.UnidadeMedida.unidade,
            entities.Produto.ativo == True
        ).scalar() or 0

        return jsonify({
            'success': True,
            'metrics': [
                {'title': "Clientes", 'value': clientes_count, 'icon': "users", 'color': "success"},
                {'title': "Produtos", 'value': produtos_count, 'icon': "box", 'color': "info"},
                {'title': "Notas Fiscais", 'value': notas_count, 'icon': "file-invoice", 'color': "warning"},
                {'title': "Estoque (kg)", 'value': f"{estoque_kg:.2f} kg", 'icon': "weight", 'color': "secondary"},
                {'title': "Estoque (sacos)", 'value': f"{estoque_saco:.2f} sacos", 'icon': "shopping-bag", 'color': "secondary"},
                {'title': "Estoque (unidades)", 'value': f"{estoque_unidade:.2f} un", 'icon': "cubes", 'color': "secondary"},
            ],
            'caixa_aberto': caixa is not None
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/dashboard/movimentacoes')
@login_required
@admin_required
def get_movimentacoes():
    try:
        movimentacoes = db.session.query(entities.MovimentacaoEstoque)\
            .order_by(entities.MovimentacaoEstoque.data.desc())\
            .limit(10)\
            .all()
        
        result = []
        for mov in movimentacoes:
            result.append({
                'data': mov.data.strftime('%d/%m/%Y'),
                'tipo': mov.tipo.value.capitalize(),
                'produto': mov.produto.nome,
                'quantidade': f"{mov.quantidade:,.2f} {mov.produto.unidade.value}",
                'valor': f"R$ {mov.valor_unitario * mov.quantidade:,.2f}"
            })
        
        return jsonify({'success': True, 'movimentacoes': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== Caixa Routes =====
@admin_bp.route('/caixa/abrir', methods=['POST'])
@login_required
@admin_required
def abrir_caixa_route():
    try:
        data = request.get_json()
        valor_abertura = Decimal(data.get('valor_abertura'))
        observacao = data.get('observacao', '')
        
        caixa = abrir_caixa(
            db.session,
            operador_id=current_user.id,
            valor_abertura=valor_abertura,
            observacao=observacao
        )
        
        return jsonify({
            'success': True,
            'message': 'Caixa aberto com sucesso',
            'caixa': {
                'id': caixa.id,
                'data_abertura': caixa.data_abertura.strftime('%d/%m/%Y %H:%M'),
                'valor_abertura': str(caixa.valor_abertura)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/caixa/fechar', methods=['POST'])
@login_required
@admin_required
def fechar_caixa_route():
    try:
        data = request.get_json()
        valor_fechamento = Decimal(data.get('valor_fechamento'))
        observacao = data.get('observacao', '')
        
        caixa = fechar_caixa(
            db.session,
            operador_id=current_user.id,
            valor_fechamento=valor_fechamento,
            observacao=observacao
        )
        
        return jsonify({
            'success': True,
            'message': 'Caixa fechado com sucesso',
            'caixa': {
                'id': caixa.id,
                'data_fechamento': caixa.data_fechamento.strftime('%d/%m/%Y %H:%M'),
                'valor_fechamento': str(caixa.valor_fechamento)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/caixa/status')
@login_required
@admin_required
def get_caixa_status():
    try:
        caixa = get_caixa_aberto(db.session)
        if caixa:
            return jsonify({
                'success': True,
                'aberto': True,
                'caixa': {
                    'id': caixa.id,
                    'data_abertura': caixa.data_abertura.strftime('%d/%m/%Y %H:%M'),
                    'valor_abertura': str(caixa.valor_abertura),
                    'operador': caixa.operador.nome
                }
            })
        else:
            return jsonify({'success': True, 'aberto': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/caixa/historico')
@login_required
@admin_required
def get_caixa_historico():
    try:
        caixas = get_caixas(db.session)
        result = []
        for caixa in caixas:
            result.append({
                'id': caixa.id,
                'data_abertura': caixa.data_abertura.strftime('%d/%m/%Y %H:%M'),
                'data_fechamento': caixa.data_fechamento.strftime('%d/%m/%Y %H:%M') if caixa.data_fechamento else None,
                'valor_abertura': str(caixa.valor_abertura),
                'valor_fechamento': str(caixa.valor_fechamento) if caixa.valor_fechamento else None,
                'status': caixa.status.value,
                'operador': caixa.operador.nome
            })
        return jsonify({'success': True, 'caixas': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== Cliente Routes =====
@admin_bp.route('/clientes', methods=['GET'])
@login_required
@admin_required
def listar_clientes():
    try:
        search = request.args.get('search', '').lower()
        clientes = get_clientes_all(db.session)
        
        result = []
        for cliente in clientes:
            if search and (search not in cliente.nome.lower() and 
                          search not in (cliente.documento or '').lower()):
                continue
                
            result.append({
                'id': cliente.id,
                'nome': cliente.nome,
                'documento': cliente.documento or '',
                'telefone': cliente.telefone or '',
                'email': cliente.email or '',
                'ativo': 'Ativo' if cliente.ativo else 'Inativo',
                'endereco': cliente.endereco or ''
            })
            
        return jsonify({'success': True, 'clientes': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/clientes', methods=['POST'])
@login_required
@admin_required
def criar_cliente():
    try:
        data = request.get_json()
        cliente_data = ClienteCreate(
            nome=data['nome'],
            documento=data.get('documento'),
            telefone=data.get('telefone'),
            email=data.get('email'),
            endereco=data.get('endereco'),
            criado_em=datetime.now(tz=ZoneInfo("America/Sao_Paulo")),
            ativo=True
        )
        
        cliente = create_cliente(db.session, cliente_data)
        return jsonify({
            'success': True,
            'message': 'Cliente criado com sucesso',
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'documento': cliente.documento,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'ativo': cliente.ativo
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_cliente(cliente_id):
    try:
        data = request.get_json()
        
        cliente_data = ClienteUpdate(
            nome=data.get('nome'),
            documento=data.get('documento'),
            telefone=data.get('telefone'),
            email=data.get('email'),
            endereco=data.get('endereco'),
            ativo=data.get('ativo')
        )
        
        cliente = update_cliente(db.session, cliente_id, cliente_data)
        return jsonify({
            'success': True,
            'message': 'Cliente atualizado com sucesso',
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'documento': cliente.documento,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'ativo': cliente.ativo
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
@login_required
@admin_required
def obter_cliente(cliente_id):
    try:
        cliente = get_cliente(db.session, cliente_id)
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        return jsonify({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'documento': cliente.documento,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'endereco': cliente.endereco,
                'ativo': cliente.ativo
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required
@admin_required
def remover_cliente(cliente_id):
    try:
        delete_cliente(db.session, cliente_id)
        return jsonify({'success': True, 'message': 'Cliente removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ===== Produto Routes =====
@admin_bp.route('/produtos', methods=['GET'])
@login_required
@admin_required
def listar_produtos():
    try:
        search = request.args.get('search', '').lower()
        produtos = get_produtos(db.session)
        
        result = []
        for produto in produtos:
            if search and (search not in produto.nome.lower() and 
                          search not in produto.tipo.lower()):
                continue
                
            result.append({
                'id': produto.id,
                'codigo': produto.codigo or '',
                'nome': produto.nome,
                'tipo': produto.tipo,
                'unidade': produto.unidade.value,
                'valor': f"R$ {produto.valor_unitario:,.2f}",
                'estoque_loja': f"{produto.estoque_loja:,.2f}",
                'estoque_deposito': f"{produto.estoque_deposito:,.2f}",
                'estoque_fabrica': f"{produto.estoque_fabrica:,.2f}",
                'marca': produto.marca or ''
            })
        
        return jsonify({'success': True, 'produtos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/produtos', methods=['POST'])
@login_required
@admin_required
def criar_produto():
    try:
        data = request.get_json()

        produto_data = ProdutoCreate(
            codigo=data.get('codigo'),
            nome=data['nome'],
            tipo=data['tipo'],
            marca=data.get('marca'),
            unidade=data['unidade'],
            valor_unitario=Decimal(data['valor_unitario']),
            valor_unitario_compra=Decimal(data.get('valor_unitario_compra', 0)),
            valor_total_compra=Decimal(data.get('valor_total_compra', 0)),
            imcs=Decimal(data.get('imcs', 0)),
            estoque_loja=Decimal(data.get('estoque_loja', 0)),
            estoque_deposito=Decimal(data.get('estoque_deposito', 0)),
            estoque_fabrica=Decimal(data.get('estoque_fabrica', 0)),
            estoque_minimo=Decimal(data.get('estoque_minimo', 0)),
            estoque_maximo=None,
            ativo=True
        )

        produto = create_produto(db.session, produto_data)
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'unidade': produto.unidade.value,
                'valor_unitario': str(produto.valor_unitario),
                'valor_unitario_compra': str(produto.valor_unitario_compra),
                'valor_total_compra': str(produto.valor_total_compra),
                'imcs': str(produto.imcs),
                'estoque_loja': str(produto.estoque_loja),
                'estoque_deposito': str(produto.estoque_deposito),
                'estoque_fabrica': str(produto.estoque_fabrica),
                'estoque_minimo': str(produto.estoque_minimo)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

def to_decimal_or_none(value):
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(value)
    value = str(value).strip()
    if value == '':
        return None
    return Decimal(value)

@admin_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_produto(produto_id):
    try:
        data = request.get_json()
        produto = get_produto(db.session, produto_id)
        
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

        # Atualizar campos básicos
        update_fields = {}
        for campo in ['codigo', 'nome', 'tipo', 'marca', 'unidade', 'ativo',
                     'valor_unitario', 'valor_unitario_compra', 'valor_total_compra',
                     'imcs', 'estoque_loja', 'estoque_deposito', 'estoque_fabrica',
                     'estoque_minimo', 'estoque_maximo']:
            if campo in data:
                valor = data[campo]
                if campo.startswith('valor_') or campo.startswith('estoque') or campo == 'imcs':
                    valor = to_decimal_or_none(valor)
                update_fields[campo] = valor

        produto_data = ProdutoUpdate(**update_fields)
        produto = update_produto(db.session, produto_id, produto_data)

        # Atualizar descontos
        try:
            produto.descontos = []
            db.session.flush()

            if 'descontos' in data and isinstance(data['descontos'], (list, tuple)):
                desconto_ids = [int(id) for id in data['descontos']] if data['descontos'] else []
            elif 'desconto_id' in data and data['desconto_id']:
                desconto_ids = [int(data['desconto_id'])]
            else:
                desconto_ids = []

            for desconto_id in desconto_ids:
                desconto = buscar_desconto_by_id(db.session, desconto_id)
                if not desconto:
                    return jsonify({
                        'success': False,
                        'message': f'Desconto com ID {desconto_id} não encontrado'
                    }), 400
                produto.descontos.append(desconto)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Erro ao atualizar descontos: {str(e)}'
            }), 400

        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso',
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'descontos': [{
                    'id': d.id,
                    'identificador': d.identificador,
                    'valor': float(d.valor),
                    'quantidade_minima': float(d.quantidade_minima),
                    'tipo': d.tipo.name
                } for d in produto.descontos]
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
        
@admin_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@login_required
@admin_required
def obter_produto(produto_id):
    try:
        produto = get_produto(db.session, produto_id)
        
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

        # Obter todos os descontos disponíveis
        todos_descontos = buscar_todos_os_descontos(db.session)
        
        # Serializar descontos disponíveis
        descontos_disponiveis = []
        for desconto in todos_descontos:
            descontos_disponiveis.append({
                "id": desconto.id,
                "identificador": desconto.identificador,
                "descricao": desconto.descricao or "",
                "tipo": desconto.tipo.name if desconto.tipo else None,
                "valor": float(desconto.valor),
                "quantidade_minima": float(desconto.quantidade_minima),
                "quantidade_maxima": float(desconto.quantidade_maxima) if desconto.quantidade_maxima else None,
                "valido_ate": desconto.valido_ate.isoformat() if desconto.valido_ate else None,
                "ativo": desconto.ativo
            })

        # Serializar descontos do produto
        descontos_produto = []
        for desconto in produto.descontos:
            descontos_produto.append({
                "id": desconto.id,
                "identificador": desconto.identificador,
                "descricao": desconto.descricao or "",
                "tipo": desconto.tipo.name if desconto.tipo else None,
                "valor": float(desconto.valor),
                "quantidade_minima": float(desconto.quantidade_minima),
                "quantidade_maxima": float(desconto.quantidade_maxima) if desconto.quantidade_maxima else None,
                "valido_ate": desconto.valido_ate.isoformat() if desconto.valido_ate else None,
                "ativo": desconto.ativo
            })

        return jsonify({
            'success': True,
            'produto': {
                'id': produto.id,
                'codigo': produto.codigo or '',
                'nome': produto.nome,
                'tipo': produto.tipo,
                'marca': produto.marca or '',
                'unidade': produto.unidade.value,
                'valor_unitario': str(produto.valor_unitario),
                'valor_unitario_compra': str(produto.valor_unitario_compra or 0),
                'valor_total_compra': str(produto.valor_total_compra or 0),
                'imcs': str(produto.imcs or 0),
                'estoque_loja': f"{float(produto.estoque_loja or 0):.2f}",
                'estoque_deposito': f"{float(produto.estoque_deposito or 0):.2f}",
                'estoque_fabrica': f"{float(produto.estoque_fabrica or 0):.2f}",
                'estoque_minimo': f"{float(produto.estoque_minimo or 0):.2f}",
                'estoque_maximo': f"{float(produto.estoque_maximo or 0):.2f}",
                'ativo': produto.ativo,
                'descontos': descontos_produto
            },
            'todos_descontos': descontos_disponiveis
        })
        print(f'{produto.id} {todos_descontos}')
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
@login_required
@admin_required
def remover_produto(produto_id):
    try:
        produto = db.session.query(entities.Produto).get(produto_id)

        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

        estoque_total = (
            float(produto.estoque_loja or 0) +
            float(produto.estoque_deposito or 0) +
            float(produto.estoque_fabrica or 0)
        )

        if estoque_total != 0:
            return jsonify({
                'success': False,
                'message': 'Não é possível remover o produto. Ainda há saldo em estoque (mesmo que negativo).'
            }), 400

        db.session.delete(produto)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Produto removido com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao remover produto.'}), 500

@admin_bp.route('/produtos/<int:produto_id>/movimentacao', methods=['POST'])
@login_required
@admin_required
def registrar_movimentacao_produto(produto_id):
    try:
        data = request.get_json()
        caixa = get_caixa_aberto(db.session)
        if not caixa:
            return jsonify({'success': False, 'message': 'Nenhum caixa aberto encontrado'}), 400
            
        mov_data = MovimentacaoEstoqueCreate(
            produto_id=produto_id,
            usuario_id=current_user.id,
            cliente_id=data.get('cliente_id'),
            caixa_id=caixa.id,
            tipo=data['tipo'],
            quantidade=Decimal(data['quantidade']),
            valor_unitario=Decimal(data['valor_unitario']),
            valor_recebido=Decimal(data.get('valor_recebido', 0)),
            troco=Decimal(data.get('troco', 0)),
            forma_pagamento=data.get('forma_pagamento'),
            observacao=data.get('observacao'),
            estoque_origem=data.get('estoque_origem', entities.TipoEstoque.loja),
            estoque_destino=data.get('estoque_destino', entities.TipoEstoque.loja)
        )
        
        movimentacao = registrar_movimentacao(db.session, mov_data)
        return jsonify({
            'success': True,
            'message': 'Movimentação registrada com sucesso',
            'movimentacao': {
                'id': movimentacao.id,
                'data': movimentacao.data.strftime('%d/%m/%Y %H:%M'),
                'tipo': movimentacao.tipo.value.capitalize(),
                'quantidade': str(movimentacao.quantidade),
                'valor_unitario': str(movimentacao.valor_unitario),
                'produto': movimentacao.produto.nome
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    
    
# ===== Venda com Data Retroativa ====
@admin_bp.route('/api/vendas/retroativa', methods=['POST'])
@login_required
@admin_required
def api_registrar_venda_retroativa():
    # Verificação inicial do conteúdo da requisição
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'Content-Type deve ser application/json'
        }), 400

    try:
        dados_venda = request.get_json()
        print(dados_venda)
        
        if dados_venda is None:
            return jsonify({
                'success': False,
                'message': 'JSON inválido ou não enviado'
            }), 400

        # Campos obrigatórios
        required_fields = ['cliente_id', 'itens', 'pagamentos', 'valor_total', 'caixa_id', 'data_emissao']
        for field in required_fields:
            if field not in dados_venda:
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório faltando: {field}'
                }), 400

        # Validar data de emissão (apenas formato e não-futura)
        try:
            data_emissao = datetime.strptime(dados_venda['data_emissao'], '%Y-%m-%d %H:%M:%S')
            if data_emissao > datetime.utcnow():
                return jsonify({
                    'success': False,
                    'message': 'Data de emissão não pode ser futura'
                }), 400
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD HH:MM:SS'
            }), 400

        # Verificar apenas se o caixa existe e está fechado
        caixa = entities.Caixa.query.get(dados_venda['caixa_id'])
        if not caixa:
            return jsonify({
                'success': False,
                'message': f'Caixa não encontrado: ID {dados_venda["caixa_id"]}'
            }), 404

        if caixa.status == 'aberto':
            return jsonify({
                'success': False,
                'message': 'Para vendas retroativas, o caixa deve estar fechado'
            }), 400

        if not isinstance(dados_venda['itens'], list) or len(dados_venda['itens']) == 0:
            return jsonify({
                'success': False,
                'message': 'Lista de itens inválida ou vazia'
            }), 400

        if not isinstance(dados_venda['pagamentos'], list) or len(dados_venda['pagamentos']) == 0:
            return jsonify({
                'success': False,
                'message': 'Lista de pagamentos inválida ou vazia'
            }), 400

        # Conversão e validação de valores
        try:
            cliente_id = int(dados_venda['cliente_id'])
            valor_total = Decimal(str(dados_venda['valor_total']))
            total_descontos = Decimal(str(dados_venda.get('total_descontos', 0)))
            
            valor_a_vista = sum(
                Decimal(str(p.get('valor'))) 
                for p in dados_venda['pagamentos'] 
                if p.get('forma_pagamento') != 'a_prazo'
            )
            
            valor_recebido = valor_a_vista
        except (ValueError, InvalidOperation) as e:
            return jsonify({
                'success': False,
                'message': 'Valores numéricos inválidos'
            }), 400

        # Verificar cliente
        cliente = entities.Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({
                'success': False,
                'message': f'Cliente não encontrado: ID {cliente_id}'
            }), 404

        # Validar itens e estoque
        for item_data in dados_venda['itens']:
            try:
                produto_id = int(item_data.get('produto_id'))
                quantidade = Decimal(str(item_data.get('quantidade')))
                valor_unitario = Decimal(str(item_data.get('valor_unitario')))
                valor_total_item = Decimal(str(item_data.get('valor_total')))
                
                produto = entities.Produto.query.get(produto_id)
                if not produto:
                    return jsonify({
                        'success': False,
                        'message': f'Produto não encontrado: ID {produto_id}'
                    }), 404

                if produto.estoque_loja < quantidade:
                    return jsonify({
                        'success': False,
                        'message': f'Estoque insuficiente para o produto: {produto.nome}'
                    }), 400

            except (ValueError, InvalidOperation, TypeError) as e:
                return jsonify({
                    'success': False,
                    'message': 'Dados do item inválidos'
                }), 400

        # Verificar soma dos pagamentos
        try:
            soma_pagamentos = sum(Decimal(str(p.get('valor'))) for p in dados_venda['pagamentos'])
            a_prazo_usado = any(p.get('forma_pagamento') == 'a_prazo' for p in dados_venda['pagamentos'])
            
            if abs(soma_pagamentos - valor_total) > Decimal('0.01'):
                msg = f'Valor recebido ({soma_pagamentos}) diferente do total da venda ({valor_total})'
                return jsonify({
                    'success': False,
                    'message': msg
                }), 400
        except (ValueError, InvalidOperation, TypeError) as e:
            return jsonify({
                'success': False,
                'message': 'Dados de pagamento inválidos'
            }), 400

        # Criar registro de Nota Fiscal
        nota = entities.NotaFiscal(
            cliente_id=cliente.id,
            operador_id=current_user.id,
            caixa_id=caixa.id,
            data_emissao=data_emissao,
            valor_total=valor_total,
            valor_desconto=total_descontos,
            tipo_desconto=None,
            status=entities.StatusNota.emitida,
            forma_pagamento=entities.FormaPagamento.dinheiro,
            valor_recebido=valor_recebido,
            troco=max(valor_recebido - valor_total, Decimal(0)) if not a_prazo_usado else Decimal(0),
            a_prazo=a_prazo_usado
        )

        # Criar Entrega, se presente
        endereco_entrega = dados_venda.get('endereco_entrega')
        if endereco_entrega and isinstance(endereco_entrega, dict):
            entrega = entities.Entrega(
                logradouro=endereco_entrega.get('logradouro', ''),
                numero=endereco_entrega.get('numero', ''),
                complemento=endereco_entrega.get('complemento', ''),
                bairro=endereco_entrega.get('bairro', ''),
                cidade=endereco_entrega.get('cidade', ''),
                estado=endereco_entrega.get('estado', ''),
                cep=endereco_entrega.get('cep', ''),
                instrucoes=endereco_entrega.get('instrucoes', ''),
                sincronizado=False
            )
            db.session.add(entrega)
            db.session.flush()
            nota.entrega_id = entrega.id

        db.session.add(nota)
        db.session.flush()

        # Criar itens da nota fiscal
        for item_data in dados_venda['itens']:
            produto_id = item_data.get('produto_id')
            produto = entities.Produto.query.get(produto_id)
            quantidade = Decimal(str(item_data.get('quantidade')))
            valor_unitario = Decimal(str(item_data.get('valor_unitario')))
            valor_total_item = Decimal(str(item_data.get('valor_total')))
            desconto_aplicado = Decimal(str(item_data.get('valor_desconto', 0)))
            
            desconto_info = item_data.get('desconto_info', {}) or {}
            tipo_desconto = desconto_info.get('tipo') if isinstance(desconto_info, dict) else None

            item_nf = entities.NotaFiscalItem(
                nota_id=nota.id,
                produto_id=produto_id,
                estoque_origem=entities.TipoEstoque.loja,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total_item,
                desconto_aplicado=desconto_aplicado,
                tipo_desconto=entities.TipoDesconto(tipo_desconto) if tipo_desconto else None,
                sincronizado=False
            )
            db.session.add(item_nf)
            produto.estoque_loja -= quantidade

        # Criar pagamentos
        pagamentos_ids = []
        valor_a_prazo = Decimal(0)
        
        for pagamento_data in dados_venda['pagamentos']:
            forma = pagamento_data.get('forma_pagamento')
            valor = Decimal(str(pagamento_data.get('valor')))
            
            pagamento_nf = entities.PagamentoNotaFiscal(
                nota_fiscal_id=nota.id,
                forma_pagamento=entities.FormaPagamento(forma),
                valor=valor,
                data=data_emissao,
                sincronizado=False
            )
            db.session.add(pagamento_nf)
            db.session.flush()
            pagamentos_ids.append(pagamento_nf.id)
            
            # Registrar no financeiro (exceto para pagamentos a prazo)
            if forma != 'a_prazo':
                financeiro = entities.Financeiro(
                    tipo=entities.TipoMovimentacao.entrada,
                    categoria=entities.CategoriaFinanceira.venda,
                    valor=valor,
                    descricao=f"Pagamento venda NF #{nota.id}",
                    cliente_id=cliente.id,
                    caixa_id=caixa.id,
                    nota_fiscal_id=nota.id,
                    pagamento_id=pagamento_nf.id,
                    data=data_emissao,
                    sincronizado=False
                )
                db.session.add(financeiro)
            else:
                valor_a_prazo += valor

        # Criar conta a receber se houver pagamento a prazo
        if a_prazo_usado and valor_a_prazo > 0:
            conta_receber = entities.ContaReceber(
                cliente_id=cliente.id,
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo NF #{nota.id}",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=data_emissao + timedelta(days=30),
                status=entities.StatusPagamento.pendente,
                sincronizado=False
            )
            db.session.add(conta_receber)

        # Definir forma de pagamento principal
        if len(dados_venda['pagamentos']) == 1:
            nota.forma_pagamento = entities.FormaPagamento(dados_venda['pagamentos'][0]['forma_pagamento'])
        else:
            nota.forma_pagamento = entities.FormaPagamento.dinheiro

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Venda retroativa registrada com sucesso',
            'nota_fiscal_id': nota.id,
            'pagamentos_ids': pagamentos_ids,
            'valor_total': float(valor_total),
            'valor_recebido': float(valor_recebido),
            'troco': float(nota.troco) if nota.troco else 0,
            'valor_a_prazo': float(valor_a_prazo) if a_prazo_usado else 0,
            'data_emissao': data_emissao.strftime('%Y-%m-%d %H:%M:%S')
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro ao registrar venda retroativa no banco',
            'error': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro inesperado ao registrar venda retroativa',
            'error': str(e)
        }), 500
        
# Rotas para carregar dados no modal
@admin_bp.route('/api/caixas/fechados', methods=['GET'])
@login_required
@admin_required
def api_caixas_fechados():
    try:
        caixas = entities.Caixa.query.filter_by(status='fechado').order_by(entities.Caixa.data_fechamento.desc()).all()
        
        caixas_data = [{
            'id': caixa.id,
            'operador': caixa.operador.nome,
            'data_abertura': caixa.data_abertura.strftime('%d/%m/%Y %H:%M'),
            'data_fechamento': caixa.data_fechamento.strftime('%d/%m/%Y %H:%M') if caixa.data_fechamento else None,
            'valor_abertura': float(caixa.valor_abertura),
            'valor_fechamento': float(caixa.valor_fechamento) if caixa.valor_fechamento else None
        } for caixa in caixas]
        
        return jsonify({
            'success': True,
            'caixas': caixas_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar caixas fechados'
        }), 500

@admin_bp.route('/api/clientes/ativos', methods=['GET'])
@login_required
@admin_required
def api_clientes_ativos():
    try:
        clientes = entities.Cliente.query.filter_by(ativo=True).order_by(entities.Cliente.nome).all()
        
        clientes_data = [{
            'id': cliente.id,
            'nome': cliente.nome,
            'documento': cliente.documento or '',
            'telefone': cliente.telefone or '',
            'limite_credito': float(cliente.limite_credito)
        } for cliente in clientes]
        
        return jsonify({
            'success': True,
            'clientes': clientes_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar clientes'
        }), 500

@admin_bp.route('/api/produtos/ativos', methods=['GET'])
@login_required
@admin_required
def api_produtos_ativos():
    try:
        produtos = entities.Produto.query.filter_by(ativo=True).order_by(entities.Produto.nome).all()
        
        produtos_data = [{
            'id': produto.id,
            'codigo': produto.codigo or '',
            'nome': produto.nome,
            'valor_unitario': float(produto.valor_unitario),
            'estoque_loja': float(produto.estoque_loja),
            'unidade': produto.unidade.value,
            'marca': produto.marca or '',
            'tipo': produto.tipo
        } for produto in produtos]
        
        return jsonify({
            'success': True,
            'produtos': produtos_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar produtos'
        }), 500
        
        
# ===== Usuário Routes =====
@admin_bp.route('/usuarios', methods=['GET'])
@login_required
@admin_required
def listar_usuarios():
    try:
        search = request.args.get('search', '').lower()
        usuarios = get_usuarios(db.session)
        
        result = []
        for usuario in usuarios:
            if search and (search not in usuario.nome.lower() and 
                          search not in usuario.email.lower()):
                continue
                
            result.append({
                'id': usuario.id,
                'nome': usuario.nome,
                'tipo': usuario.tipo.value.capitalize(),
                'status': 'Ativo' if usuario.status else 'Inativo',
                'ultimo_acesso': usuario.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if usuario.ultimo_acesso else 'Nunca',
                'cpf': usuario.cpf
            })
        
        return jsonify({'success': True, 'usuarios': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
@login_required
@admin_required
def get_usuario(usuario_id):
    try:
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            return jsonify({
                'success': False, 
                'message': 'Usuário não encontrado',
                'error': 'not_found'
            }), 404
        
        # Verificar se o tipo é um Enum antes de acessar .value
        tipo_usuario = usuario.tipo.value if hasattr(usuario.tipo, 'value') else usuario.tipo
        
        # Formatar datas corretamente
        ultimo_acesso = usuario.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if usuario.ultimo_acesso else None
        data_cadastro = usuario.criado_em.strftime('%d/%m/%Y %H:%M') if usuario.criado_em else None
        
        return jsonify({
            'success': True,
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome,
                'cpf': usuario.cpf,
                'tipo': tipo_usuario,
                'status': bool(usuario.status),  # Garantir que é booleano
                'ultimo_acesso': ultimo_acesso,
                'data_cadastro': data_cadastro,
                'observacoes': usuario.observacoes or ''  # Garantir string vazia se None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro interno ao carregar dados do usuário',
            'error': str(e)
        }), 500

@admin_bp.route('/usuarios', methods=['POST'])
@login_required
@admin_required
def criar_usuario():
    try:
        data = request.get_json()

        usuario_data = UsuarioCreate(
            nome=data['nome'],
            cpf=data['cpf'],
            senha=data['senha'],
            tipo=data['tipo'],
            status=data.get('status', True),
            observacoes=data.get('observacoes')
        )

        novo_usuario = create_user(db.session, usuario_data)

        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'usuario': {
                'id': novo_usuario.id,
                'nome': novo_usuario.nome,
                'cpf': novo_usuario.cpf,
                'tipo': novo_usuario.tipo.value,
                'status': novo_usuario.status,
                'observacoes': novo_usuario.observacoes
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_usuario(usuario_id):
    try:
        data = request.get_json()
        
        # Verificar se foi enviada senha e confirmação
        if 'senha' in data or 'confirma_senha' in data:
            if 'senha' not in data or 'confirma_senha' not in data:
                raise ValueError("Para alterar a senha, ambos os campos 'senha' e 'confirma_senha' devem ser enviados")
            if data['senha'] != data['confirma_senha']:
                raise ValueError("As senhas não coincidem")
        
        # Criar o objeto de atualização removendo campos não relevantes
        update_data = {k: v for k, v in data.items() if k not in ['confirma_senha']}
        
        usuario_data = UsuarioUpdate(**update_data)
        
        usuario = update_user(db.session, usuario_id, usuario_data)
        return jsonify({
            'success': True,
            'message': 'Usuário atualizado com sucesso',
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome,
                'cpf': usuario.cpf,
                'tipo': usuario.tipo.value,
                'status': usuario.status,
                'observacoes': usuario.observacoes
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@login_required
@admin_required
def remover_usuario(usuario_id):
    try:
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404

        db.session.delete(usuario)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuário removido com sucesso'})

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Não é possível remover o usuário. Ele está vinculado a um ou mais caixas.'
        }), 400

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro inesperado ao remover o usuário. Tente novamente mais tarde.'
        }), 500


# ===== Financeiro Routes =====
@admin_bp.route('/financeiro', methods=['GET'])
@login_required
@admin_required
def listar_financeiro():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        categoria = request.args.get('categoria')
        tipo = request.args.get('tipo')
        caixa_id = request.args.get('caixa_id')
        
        # Convert dates if provided
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') if data_fim else None
        
        lancamentos = get_lancamentos_financeiros(
            db.session,
            tipo=tipo,
            categoria=categoria,
            data_inicio=dt_inicio,
            data_fim=dt_fim,
            caixa_id=int(caixa_id) if caixa_id else None
        )
        
        receitas = 0
        despesas = 0
        
        result = []
        for lanc in lancamentos:
            valor = float(lanc.valor)
            if lanc.tipo == 'entrada':
                receitas += valor
            else:
                despesas += valor
                
            result.append({
                'data': lanc.data.strftime('%d/%m/%Y'),
                'tipo': lanc.tipo.value.capitalize(),
                'categoria': lanc.categoria.value.capitalize(),
                'valor': f"R$ {valor:,.2f}",
                'descricao': lanc.descricao,
                'nota': lanc.nota_fiscal_id or '-',
                'cor': 'success' if lanc.tipo == 'entrada' else 'danger'
            })
        
        saldo = receitas - despesas
        
        return jsonify({
            'success': True,
            'lancamentos': result,
            'resumo': {
                'receitas': f"R$ {receitas:,.2f}",
                'despesas': f"R$ {despesas:,.2f}",
                'saldo': f"R$ {saldo:,.2f}"
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/financeiro', methods=['POST'])
@login_required
@admin_required
def criar_lancamento_financeiro():
    try:
        data = request.get_json()
        
        lancamento_data = FinanceiroCreate(
            tipo=data['tipo'],
            categoria=data['categoria'],
            valor=Decimal(data['valor']),
            descricao=data.get('descricao', ''),
            data=datetime.now(tz=ZoneInfo("America/Sao_Paulo")),
            nota_fiscal_id=data.get('nota_fiscal_id'),
            cliente_id=data.get('cliente_id'),
            caixa_id=data.get('caixa_id')
        )
        
        lancamento = create_lancamento_financeiro(db.session, lancamento_data)
        return jsonify({
            'success': True,
            'message': 'Lançamento financeiro criado com sucesso',
            'lancamento': {
                'id': lancamento.id,
                'tipo': lancamento.tipo.value,
                'categoria': lancamento.categoria.value,
                'valor': str(lancamento.valor),
                'descricao': lancamento.descricao
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/financeiro/<int:lancamento_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_lancamento_financeiro(lancamento_id):
    try:
        data = request.get_json()
        
        lancamento_data = FinanceiroUpdate(
            tipo=data.get('tipo'),
            categoria=data.get('categoria'),
            valor=Decimal(data['valor']) if 'valor' in data else None,
            descricao=data.get('descricao')
        )
        
        lancamento = update_lancamento_financeiro(db.session, lancamento_id, lancamento_data)
        return jsonify({
            'success': True,
            'message': 'Lançamento financeiro atualizado com sucesso',
            'lancamento': {
                'id': lancamento.id,
                'tipo': lancamento.tipo.value,
                'categoria': lancamento.categoria.value,
                'valor': str(lancamento.valor),
                'descricao': lancamento.descricao
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/financeiro/<int:lancamento_id>', methods=['DELETE'])
@login_required
@admin_required
def remover_lancamento_financeiro(lancamento_id):
    try:
        delete_lancamento_financeiro(db.session, lancamento_id)
        return jsonify({'success': True, 'message': 'Lançamento financeiro removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ===== Nota Fiscal Routes =====
@admin_bp.route('/notas-fiscais', methods=['POST'])
@login_required
def criar_nota_fiscal():
    try:
        data = request.get_json()
        caixa = get_caixa_aberto(db.session)
        if not caixa:
            return jsonify({'success': False, 'message': 'Nenhum caixa aberto encontrado'}), 400
            
        nota_data = {
            'cliente_id': data.get('cliente_id'),
            'operador_id': current_user.id,
            'caixa_id': caixa.id,
            'valor_total': Decimal(data['valor_total']),
            'forma_pagamento': data['forma_pagamento'],
            'valor_recebido': Decimal(data.get('valor_recebido', data['valor_total'])),
            'troco': Decimal(data.get('troco', 0)),
            'observacao': data.get('observacao', ''),
            'itens': data['itens']
        }
        
        nota = create_nota_fiscal(db.session, nota_data)
        return jsonify({
            'success': True,
            'message': 'Nota fiscal criada com sucesso',
            'nota': {
                'id': nota.id,
                'numero': nota.id,
                'data': nota.data_emissao.strftime('%d/%m/%Y %H:%M'),
                'valor_total': str(nota.valor_total),
                'cliente': nota.cliente.nome if nota.cliente else 'Consumidor'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/notas-fiscais', methods=['GET'])
@login_required
@admin_required
def listar_notas_fiscais():
    try:
        notas = get_notas_fiscais(db.session)
        result = []
        for nota in notas:
            result.append({
                'id': nota.id,
                'data': nota.data_emissao.strftime('%d/%m/%Y %H:%M'),
                'cliente': nota.cliente.nome if nota.cliente else 'Consumidor',
                'valor': f"R$ {nota.valor_total:,.2f}",
                'status': nota.status.value.capitalize(),
                'forma_pagamento': nota.forma_pagamento.value.replace('_', ' ').capitalize()
            })
        
        return jsonify({'success': True, 'notas': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/notas-fiscais/<int:nota_id>', methods=['GET'])
@login_required
@admin_required
def detalhar_nota_fiscal(nota_id):
    try:
        nota = get_nota_fiscal(db.session, nota_id)
        if not nota:
            return jsonify({'success': False, 'message': 'Nota fiscal não encontrada'}), 404
            
        itens = []
        for item in nota.itens:
            itens.append({
                'produto': item.produto.nome,
                'quantidade': str(item.quantidade),
                'valor_unitario': f"R$ {item.valor_unitario:,.2f}",
                'valor_total': f"R$ {item.valor_total:,.2f}"
            })
            
        return jsonify({
            'success': True,
            'nota': {
                'id': nota.id,
                'data': nota.data_emissao.strftime('%d/%m/%Y %H:%M'),
                'cliente': nota.cliente.nome if nota.cliente else 'Consumidor',
                'valor_total': f"R$ {nota.valor_total:,.2f}",
                'status': nota.status.value.capitalize(),
                'forma_pagamento': nota.forma_pagamento.value.replace('_', ' ').capitalize(),
                'valor_recebido': f"R$ {nota.valor_recebido:,.2f}",
                'troco': f"R$ {nota.troco:,.2f}",
                'operador': nota.operador.nome,
                'itens': itens
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@admin_bp.route('/transferencias', methods=['POST'])
@login_required
@admin_required
def criar_transferencia():
    try:
        data = request.get_json()
        # Campos obrigatórios básicos
        required_keys = [
            'produto_id', 'estoque_origem', 'estoque_destino', 
            'quantidade', 'valor_unitario_destino'
        ]
        
        if not all(k in data and data[k] not in [None, ''] for k in required_keys):
            return jsonify({'success': False, 'message': 'Dados incompletos para a transferência'}), 400

        # Validações e conversões
        produto_id = int(data['produto_id'])
        quantidade = Decimal(str(data['quantidade']))
        estoque_origem = TipoEstoque(data['estoque_origem'])
        estoque_destino = TipoEstoque(data['estoque_destino'])
        valor_unitario_destino = Decimal(str(data['valor_unitario_destino']))
        observacao = data.get('observacao', '')
        converter_unidade = data.get('converter_unidade', False)
        
        if quantidade <= 0:
            return jsonify({'success': False, 'message': 'Quantidade deve ser maior que zero'}), 400
        
        if estoque_origem == estoque_destino:
            return jsonify({'success': False, 'message': 'Estoque de origem e destino devem ser diferentes'}), 400

        transferencia_data = {
            'produto_id': produto_id,
            'usuario_id': current_user.id,
            'estoque_origem': estoque_origem,
            'estoque_destino': estoque_destino,
            'quantidade': quantidade,
            'valor_unitario_destino': valor_unitario_destino,
            'observacao': observacao,
            'converter_unidade': converter_unidade
        }

        transferencia = registrar_transferencia(db.session, transferencia_data)

        return jsonify({
            'success': True,
            'message': 'Transferência realizada com sucesso',
            'transferencia': {
                'id': transferencia.id,
                'data': transferencia.data.strftime('%d/%m/%Y %H:%M'),
                'produto': transferencia.produto.nome,
                'origem': transferencia.estoque_origem.value,
                'destino': transferencia.estoque_destino.value,
                'quantidade': f"{transferencia.quantidade:.2f}",
                'unidade': transferencia.unidade_origem
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    
@admin_bp.route('/transferencias')
@login_required
@admin_required
def listar_transferencias():
    try:
        transferencias = get_transferencias(db.session)
        result = []
        for transf in transferencias:
            result.append({
                'id': transf.id,
                'data': transf.data.strftime('%d/%m/%Y %H:%M'),
                'produto': transf.produto.nome,
                'origem': transf.estoque_origem.value,
                'destino': transf.estoque_destino.value,
                'quantidade': f"{transf.quantidade:.2f}",
                'usuario': transf.usuario.nome, 
                'observacao': transf.observacao or ''
            })
        
        return jsonify({'success': True, 'transferencias': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/descontos', methods=['POST'])
@login_required
@admin_required
def criar_desconto_route():
    dados = request.get_json()
    
    # Validação básica dos dados - mantendo os nomes das variáveis originais
    required_fields = ['identificador', 'quantidade_minima', 'quantidade_maxima', 'valor_unitario_com_desconto']
    if not all(field in dados for field in required_fields):
        return jsonify({'erro': 'Campos obrigatórios faltando'}), 400
    
    try:
        session = Session(db.engine)
        # Mapeando os campos mantendo os nomes das variáveis originais
        dados_desconto = {
            'identificador': dados['identificador'],
            'quantidade_minima': dados['quantidade_minima'],
            'quantidade_maxima': dados.get('quantidade_maxima'),
            'valor': dados['valor_unitario_com_desconto'],  # Mapeando para o campo 'valor' do modelo
            'tipo': entities.TipoDesconto.fixo,  # Definindo como fixo para manter compatibilidade
            'descricao': dados.get('descricao', ''),
            'valido_ate': dados.get('valido_ate'),
            'ativo': dados.get('ativo', True)
        }
        
        desconto = criar_desconto(session, dados_desconto)
        return jsonify({
            'success': True,
            'mensagem': 'Desconto criado com sucesso',
            'desconto': {
                'id': desconto.id,
                'identificador': desconto.identificador,
                'quantidade_minima': float(desconto.quantidade_minima),
                'quantidade_maxima': float(desconto.quantidade_maxima),
                'valor_unitario_com_desconto': float(desconto.valor),  # Retornando o valor como valor_unitario_com_desconto
                'valido_ate': desconto.valido_ate.isoformat() if desconto.valido_ate else None,
                'ativo': desconto.ativo,
                'criado_em': desconto.criado_em.isoformat()
            }
        }), 201
    except Exception as e:
        print(f"Erro ao criar desconto: {e}")
        return jsonify({'erro': str(e)}), 500
    finally:
        session.close()

@admin_bp.route('/descontos/produto/<int:produto_id>', methods=['GET'])
@login_required
def buscar_descontos_produto_route(produto_id):
    try:
        session = Session(db.engine)
        descontos = buscar_descontos_por_produto_id(session, produto_id)
        
        return jsonify({
            'success': True,
            'descontos': [{
                'id': d.id,
                'produto_id': produto_id,  # Mantendo o nome do parâmetro
                'produto_nome': d.produto.nome if d.produto else None,
                'quantidade_minima': float(d.quantidade_minima),
                'quantidade_maxima': float(d.quantidade_maxima),
                'valor_unitario_com_desconto': float(d.valor),  # Mapeando valor para valor_unitario_com_desconto
                'valido_ate': d.valido_ate.isoformat() if d.valido_ate else None,
                'ativo': d.ativo,
                'criado_em': d.criado_em.isoformat()
            } for d in descontos]
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        session.close()

@admin_bp.route('/descontos/<int:desconto_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_desconto_route(desconto_id):
    dados = request.get_json()

    try:
        session = Session(db.engine)
        # Mapeando os campos mantendo os nomes das variáveis originais
        dados_atualizacao = {
            'identificador': dados.get('identificador'),
            'quantidade_minima': dados.get('quantidade_minima'),
            'quantidade_maxima': dados.get('quantidade_maxima'),
            'valor': dados.get('valor_unitario_com_desconto'),  # Mapeando para o campo 'valor' do modelo
            'descricao': dados.get('descricao'),
            'valido_ate': dados.get('valido_ate'),
            'ativo': dados.get('ativo')
        }
        
        desconto = atualizar_desconto(session, desconto_id, dados_atualizacao)

        if not desconto:
            return jsonify({
                'success': False,
                'erro': 'Desconto não encontrado'
            }), 404

        return jsonify({
            'success': True,
            'mensagem': 'Desconto atualizado com sucesso',
            'desconto': {
                'id': desconto.id,
                'identificador': desconto.identificador,
                'descricao': desconto.descricao,
                'quantidade_minima': float(desconto.quantidade_minima),
                'quantidade_maxima': float(desconto.quantidade_maxima),
                'valor_unitario_com_desconto': float(desconto.valor),  # Mapeando valor para valor_unitario_com_desconto
                'valido_ate': desconto.valido_ate.isoformat() if desconto.valido_ate else None,
                'ativo': desconto.ativo,
                'atualizado_em': desconto.atualizado_em.isoformat()
            }
        }), 200
    except Exception as e:
        print(f"Erro ao atualizar desconto: {e}")
        return jsonify({
            'success': False,
            'erro': 'Erro interno ao tentar atualizar o desconto. Por favor, tente novamente mais tarde.'
        }), 500
    finally:
        session.close()

@admin_bp.route('/descontos/<int:desconto_id>', methods=['DELETE'])
@login_required
@admin_required
def deletar_desconto_route(desconto_id):
    try:
        session = Session(db.engine)
        
        sucesso = deletar_desconto(session, desconto_id)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Desconto deletado com sucesso'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Desconto não encontrado'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        session.close()

@admin_bp.route('/descontos', methods=['GET'])
@login_required
def listar_descontos_route():
    try:
        session = Session(db.engine)
        descontos = session.query(entities.Desconto)\
            .order_by(entities.Desconto.identificador)\
            .all()

        return jsonify({
            'success': True,
            'descontos': [{
                'id': d.id,
                'identificador': d.identificador,
                'descricao': d.descricao,
                'quantidade_minima': float(d.quantidade_minima),
                'quantidade_maxima': float(d.quantidade_maxima) if d.quantidade_maxima else None,
                'valor': float(d.valor),
                'tipo': d.tipo.name,
                'valido_ate': d.valido_ate.isoformat() if d.valido_ate else None,
                'ativo': d.ativo,
                'criado_em': d.criado_em.isoformat()
            } for d in descontos]
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        session.close()

@admin_bp.route('/descontos/<int:desconto_id>', methods=['GET'])
@login_required
def buscar_desconto_por_id(desconto_id):
    try:
        session = Session(db.engine)
        desconto = session.query(entities.Desconto).get(desconto_id)
        
        if not desconto:
            return jsonify({'erro': 'Desconto não encontrado'}), 404
        
        valido_ate_formatado = desconto.valido_ate.strftime('%Y-%m-%d') if desconto.valido_ate else None
        
        return jsonify({
            'success': True,
            'desconto': {
                'id': desconto.id,
                'identificador': desconto.identificador,
                'quantidade_minima': float(desconto.quantidade_minima),
                'quantidade_maxima': float(desconto.quantidade_maxima),
                'valor_unitario_com_desconto': formatar_valor_br(desconto.valor),  # Mapeando valor para valor_unitario_com_desconto
                'descricao': desconto.descricao,
                'valido_ate': valido_ate_formatado,
                'ativo': desconto.ativo,
                'criado_em': formatar_data_br(desconto.criado_em)
            }
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        session.close()
        
@admin_bp.route('/caixas')
@login_required
@admin_required
def get_caixas():
    session = Session(db.engine)
    resultado = obter_caixas_completo(session)
    
    if resultado['success']:
        return jsonify({
            'success': True,
            'data': resultado['data'],
            'count': len(resultado['data'])
        })
    else:
        return jsonify({'success': False, 'error': resultado['message']}), 500

@admin_bp.route('/caixas/<int:caixa_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_caixa_route(caixa_id):
    try:
        dados = request.get_json()
        print(f"Dados recebidos para atualização do caixa {caixa_id}: {dados}")
        if not dados:
            return jsonify({"error": "Dados não fornecidos"}), 400
            
        caixa = db.session.get(entities.Caixa, caixa_id)
        if not caixa:
            return jsonify({"error": "Caixa não encontrado"}), 404
        
        # Atualiza status e datas conforme ação
        if 'status' in dados:
            if dados['status'] == 'fechado':
                caixa.status = entities.StatusCaixa.fechado
                caixa.data_fechamento = datetime.utcnow()
            elif dados['status'] == 'analise':
                caixa.status = entities.StatusCaixa.analise
                caixa.data_analise = datetime.utcnow()
        
        if 'valor_fechamento' in dados:
            caixa.valor_fechamento = Decimal(dados['valor_fechamento'])
        if 'valor_abertura' in dados:
            caixa.valor_abertura = Decimal(dados['valor_abertura'])
            
        # Atualiza observações se existirem
        if 'observacoes_admin' in dados:
            caixa.observacoes_admin = dados['observacoes_admin']
        
        db.session.commit()
        
        return jsonify({
            "message": "Caixa atualizado com sucesso",
            "caixa": {
                "id": caixa.id,
                "status": caixa.status.value,
                "data_analise": caixa.data_analise.isoformat() if caixa.data_analise else None,
                "data_fechamento": caixa.data_fechamento.isoformat() if caixa.data_fechamento else None,
                "observacoes_admin": caixa.observacoes_admin
            }
        }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao atualizar caixa: {str(e)}"}), 500

@admin_bp.route('/caixas/<int:caixa_id>', methods=['GET', 'PUT'])
@login_required
@admin_required
def caixa_detail(caixa_id):
    if request.method == 'GET':
        try:
            session = Session(db.engine)
            caixa = session.get(entities.Caixa, caixa_id)
            
            if not caixa:
                return jsonify({"success": False, "error": "Caixa não encontrado"}), 404
            
            # Convert caixa object to dictionary
            caixa_data = {
                'id': caixa.id,
                'operador': {
                    'id': caixa.operador.id,
                    'nome': caixa.operador.nome,
                    'tipo': caixa.operador.tipo
                },
                'data_abertura': caixa.data_abertura.isoformat(),
                'data_fechamento': caixa.data_fechamento.isoformat() if caixa.data_fechamento else None,
                'valor_abertura': float(caixa.valor_abertura),
                'valor_fechamento': float(caixa.valor_fechamento) if caixa.valor_fechamento else None,
                'status': caixa.status.value,
                'observacoes_operador': caixa.observacoes_operador,
                'observacoes_admin': caixa.observacoes_admin
            }
            
            return jsonify({"success": True, "data": caixa_data})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            dados = request.get_json()
            if not dados:
                return jsonify({"success": False, "error": "Dados não fornecidos"}), 400
                
            caixa = db.session.get(entities.Caixa, caixa_id)
            if not caixa:
                return jsonify({"success": False, "error": "Caixa não encontrado"}), 404
            
            # Atualiza status e datas conforme ação
            if 'status' in dados:
                if dados['status'] == 'fechado' and caixa.status != entities.StatusCaixa.fechado:
                    caixa.status = entities.StatusCaixa.fechado
                    caixa.data_fechamento = datetime.utcnow()
                elif dados['status'] == 'analise' and caixa.status != entities.StatusCaixa.analise:
                    caixa.status = entities.StatusCaixa.analise
                    caixa.data_analise = datetime.utcnow()
            
            # Atualiza observações se existirem
            if 'observacoes_operador' in dados:
                caixa.observacoes_operador = dados['observacoes_operador']
            if 'observacoes_admin' in dados:
                caixa.observacoes_admin = dados['observacoes_admin']
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Caixa atualizado com sucesso",
                "data": {
                    "id": caixa.id,
                    "status": caixa.status.value,
                    "data_analise": caixa.data_analise.isoformat() if caixa.data_analise else None,
                    "data_fechamento": caixa.data_fechamento.isoformat() if caixa.data_fechamento else None,
                }
            })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Erro ao atualizar caixa: {str(e)}"}), 500
        
@admin_bp.route('/caixas/<int:caixa_id>/financeiro')
@login_required
@admin_required
def get_caixa_financeiro(caixa_id):
    try:
        session = Session(db.engine)
        
        # Busca as movimentações financeiras do caixa
        movimentacoes = session.query(entities.Financeiro)\
            .filter_by(caixa_id=caixa_id)\
            .order_by(entities.Financeiro.data.desc())\
            .all()
        
        # Formata os dados para resposta
        dados = [{
            'id': mov.id,
            'data': mov.data.isoformat(),
            'tipo': mov.tipo.value,
            'categoria': mov.categoria.value if mov.categoria else None,
            'valor': float(mov.valor),
            'descricao': mov.descricao,
            'nota_fiscal_id': mov.nota_fiscal_id,
            'cliente_id': mov.cliente_id,
            'conta_receber_id': mov.conta_receber_id
        } for mov in movimentacoes]
        
        # Calcula totais
        total_entradas = sum(mov.valor for mov in movimentacoes if mov.tipo == entities.TipoMovimentacao.entrada)
        total_saidas = sum(mov.valor for mov in movimentacoes if mov.tipo == entities.TipoMovimentacao.saida)
        
        return jsonify({
            'success': True,
            'data': dados,
            'totais': {
                'entradas': float(total_entradas),
                'saidas': float(total_saidas),
                'saldo': float(total_entradas - total_saidas)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
        
@admin_bp.route('/caixas/<int:caixa_id>/aprovar', methods=['POST'])
@login_required
@admin_required
def aprovar_caixa(caixa_id):
    """Rota para aprovar o fechamento de um caixa"""
    caixa = entities.Caixa.query.get_or_404(caixa_id)
    
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Apenas administradores podem aprovar caixas'}), 403
    
    data = request.get_json()
    valor_confirmado = data.get('valor_confirmado')
    observacoes = data.get('observacoes')
    
    try:
        caixa.aprovar_fechamento(
            administrador_id=current_user.id,
            valor_confirmado=valor_confirmado,
            observacoes_admin=observacoes
        )
        db.session.commit()
        return jsonify({
            'message': 'Caixa aprovado com sucesso',
            'status': caixa.status.value,
            'valor_confirmado': float(caixa.valor_confirmado) if caixa.valor_confirmado else None
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao aprovar caixa: {str(e)}'}), 500

@admin_bp.route('/caixas/<int:caixa_id>/recusar', methods=['POST'])
@login_required
@admin_required
def recusar_caixa(caixa_id):
    """Rota para recusar o fechamento de um caixa"""
    caixa = entities.Caixa.query.get_or_404(caixa_id)
    
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Apenas administradores podem recusar caixas'}), 403
    
    data = request.get_json()
    motivo = data.get('motivo')
    valor_correto = data.get('valor_correto')
    
    if not motivo:
        return jsonify({'error': 'Motivo da recusa é obrigatório'}), 400
    
    try:
        caixa.rejeitar_fechamento(
            administrador_id=current_user.id,
            motivo=motivo,
            valor_correto=valor_correto
        )
        db.session.commit()
        return jsonify({
            'message': 'Caixa recusado com sucesso',
            'status': caixa.status.value,
            'observacoes_admin': caixa.observacoes_admin
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao recusar caixa: {str(e)}'}), 500

@admin_bp.route('/caixas/<int:caixa_id>/enviar_analise', methods=['POST'])
@login_required
@admin_required
def enviar_para_analise(caixa_id):
    """Rota para enviar um caixa para análise (fechamento inicial)"""
    print(f"Recebendo solicitação para caixa {caixa_id}")  # Log de depuração
    
    try:
        caixa = entities.Caixa.query.get_or_404(caixa_id)
        print(f"Caixa encontrado: {caixa.id}, status: {caixa.status}")  # Log de depuração
        
        data = request.get_json()
        print(f"Dados recebidos: {data}")  # Log de depuração
        
        valor_fechamento = data.get('valor_fechamento')
        observacoes = data.get('observacoes')
        
        if not valor_fechamento:
            print("Erro: Valor de fechamento não fornecido")  # Log de depuração
            return jsonify({'error': 'Valor de fechamento é obrigatório'}), 400
        
        # Adicione mais logs para verificar o usuário atual
        print(f"Usuário atual: {current_user.id}, Tipo: {current_user.tipo}")
        
        caixa.fechar_caixa(
            valor_fechamento=valor_fechamento,
            observacoes_operador=observacoes,
            usuario_id=current_user.id
        )
        db.session.commit()
        
        print("Caixa enviado para análise com sucesso")  # Log de depuração
        return jsonify({
            'message': 'Caixa enviado para análise com sucesso',
            'status': caixa.status.value,
            'valor_fechamento': float(caixa.valor_fechamento)
        }), 200
        
    except ValueError as e:
        print(f"Erro de valor: {str(e)}")  # Log de depuração
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro interno: {str(e)}")  # Log de depuração
        return jsonify({'error': f'Erro ao enviar caixa para análise: {str(e)}'}), 500

@admin_bp.route('/caixas/<int:caixa_id>/reabrir', methods=['POST'])
@login_required
@admin_required
def reabrir_caixa(caixa_id):
    """Rota para reabrir um caixa fechado ou recusado"""
    caixa = entities.Caixa.query.get_or_404(caixa_id)
    
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Apenas administradores podem reabrir caixas'}), 403
    
    data = request.get_json()
    motivo = data.get('motivo')
    
    try:
        caixa.reabrir_caixa(
            administrador_id=current_user.id,
            motivo=motivo
        )
        db.session.commit()
        return jsonify({
            'message': 'Caixa reaberto com sucesso',
            'status': caixa.status.value
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao reabrir caixa: {str(e)}'}), 500