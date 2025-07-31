from functools import wraps
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
import traceback

from sqlalchemy import func
from app import schemas
from app.models import db
from app.models import entities
from app.crud import (
    TipoEstoque, get_caixa_aberto, abrir_caixa, fechar_caixa, get_caixas, get_caixa_by_id, get_transferencias,
    get_user_by_cpf, get_user_by_id, get_usuarios, create_user, registrar_transferencia, update_user,
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
        print(f"Error fetching dashboard metrics: {e}")
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
                'quantidade': f"{mov.quantidade} {mov.produto.unidade.value}",
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
        print("Dados recebidos:", data)

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
        print("Dados recebidos para atualização:", data)

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

        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso',
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'unidade': produto.unidade.value,
                'valor_unitario': str(produto.valor_unitario),
                'valor_unitario_compra': str(produto.valor_unitario_compra),
                'valor_total_compra': str(produto.valor_total_compra),
                'imcs': str(produto.imcs),
                'estoque_loja': str(produto.estoque_loja)
            }
        })
    except Exception as e:
        print("Erro ao atualizar produto:", e)
        return jsonify({'success': False, 'message': str(e)}), 400



@admin_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@login_required
@admin_required
def obter_produto(produto_id):
    try:
        produto = get_produto(db.session, produto_id)
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

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
                'estoque_loja': str(produto.estoque_loja),
                'estoque_deposito': str(produto.estoque_deposito),
                'estoque_fabrica': str(produto.estoque_fabrica),
                'estoque_minimo': str(produto.estoque_minimo),
                'estoque_maximo': str(produto.estoque_maximo or ''),
                'ativo': produto.ativo
            }
        })
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
        print(f"Error fetching users: {e}")
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
        print(f"Erro ao buscar usuário {usuario_id}: {str(e)}")
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
        print("Recebido:", data)

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
        print("Erro ao criar usuário:", e)
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_usuario(usuario_id):
    try:
        data = request.get_json()
        print(data)
        
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
        print(f"Erro ao atualizar usuário: {e}")
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
        # Isso é opcional — para você ver os detalhes no terminal/log
        print("Erro inesperado ao excluir usuário:")
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
        print("Dados recebidos:", data)

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
                'quantidade': str(transferencia.quantidade),
                'unidade': transferencia.unidade_origem
            }
        })
    except Exception as e:
        print(f"Erro ao registrar transferência: {str(e)}")
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
                'quantidade': str(transf.quantidade),
                'usuario': transf.usuario.nome, 
                'observacao': transf.observacao or ''
            })
        
        return jsonify({'success': True, 'transferencias': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
