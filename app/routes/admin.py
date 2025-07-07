from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from app import schemas
from app.models import db
from app.models import entities
from app.crud import (
    get_caixa_aberto, abrir_caixa, fechar_caixa, get_caixas, get_caixa_by_id,
    get_user_by_cpf, get_user_by_id, get_usuarios, create_user,
    get_produto, get_produtos, create_produto, update_produto, delete_produto,
    registrar_movimentacao, get_cliente, get_clientes, create_cliente, 
    update_cliente, delete_cliente, create_nota_fiscal, get_nota_fiscal, 
    get_notas_fiscais, create_lancamento_financeiro, get_lancamento_financeiro,
    get_lancamentos_financeiros, update_lancamento_financeiro, 
    delete_lancamento_financeiro
)
from app.schemas import (
    UsuarioCreate, ProdutoCreate, ProdutoUpdate, MovimentacaoEstoqueCreate,
    ClienteCreate, ClienteBase
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ===== Dashboard Routes =====
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard_admin.html')

@admin_bp.route('/dashboard/metrics')
@login_required
def get_dashboard_metrics():
    try:
        # Get current open cash register
        caixa = get_caixa_aberto(db.session)
        
        # Count clients - Correção aqui
        clientes_count = db.session.query(entities.Cliente).filter(entities.Cliente.ativo == True).count()
        
        # Count products - Correção aqui
        produtos_count = db.session.query(entities.Produto).filter(entities.Produto.ativo == True).count()
        
        # Count invoices - Correção aqui
        notas_count = db.session.query(entities.NotaFiscal).count()
        
        # Calculate total stock - Correção aqui
        estoque_total = db.session.query(
            func.sum(entities.Produto.estoque_quantidade)
        ).filter(entities.Produto.ativo == True).scalar() or 0
        
        return jsonify({
            'success': True,
            'metrics': [
                {'title': "Clientes", 'value': clientes_count, 'icon': "users", 'color': "success"},
                {'title': "Produtos", 'value': produtos_count, 'icon': "box", 'color': "info"},
                {'title': "Notas Fiscais", 'value': notas_count, 'icon': "file-invoice", 'color': "warning"},
                {'title': "Estoque Total", 'value': f"{estoque_total} kg", 'icon': "chart-bar", 'color': "secondary"}
            ],
            'caixa_aberto': caixa is not None
        })
    except Exception as e:
        print(f"Error fetching dashboard metrics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    
@admin_bp.route('/dashboard/movimentacoes')
@login_required
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
def listar_clientes():
    try:
        search = request.args.get('search', '').lower()
        clientes = get_clientes(db.session)
        
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
                'status': 'Ativo' if cliente.ativo else 'Inativo',
                'endereco': cliente.endereco or ''
            })
        
        return jsonify({'success': True, 'clientes': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/clientes', methods=['POST'])
@login_required
def criar_cliente():
    try:
        data = request.get_json()
        cliente_data = ClienteCreate(
            nome=data['nome'],
            documento=data.get('documento'),
            telefone=data.get('telefone'),
            email=data.get('email'),
            endereco=data.get('endereco'),
            criado_em=datetime.now(tz=ZoneInfo("America/Sao_Paulo"))
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
                'status': 'Ativo'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
@login_required
def atualizar_cliente(cliente_id):
    try:
        data = request.get_json()
        cliente_data = ClienteBase(
            nome=data['nome'],
            documento=data.get('documento'),
            telefone=data.get('telefone'),
            email=data.get('email'),
            endereco=data.get('endereco')
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
                'status': 'Ativo' if cliente.ativo else 'Inativo'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
@login_required
def obter_cliente(cliente_id):
    try:
        cliente = get_cliente(db.session, cliente_id)  # implemente essa função se necessário

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
                'status': 'Ativo' if cliente.ativo else 'Inativo'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required
def remover_cliente(cliente_id):
    try:
        delete_cliente(db.session, cliente_id)
        return jsonify({'success': True, 'message': 'Cliente removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ===== Produto Routes =====
@admin_bp.route('/produtos', methods=['GET'])
@login_required
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
                'estoque': f"{produto.estoque_quantidade} {produto.unidade.value}",
                'marca': produto.marca or ''
            })
        
        return jsonify({'success': True, 'produtos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/produtos', methods=['POST'])
@login_required
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
            estoque_quantidade=Decimal(data['estoque_quantidade'])
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
                'valor': str(produto.valor_unitario),
                'estoque': str(produto.estoque_quantidade)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
@login_required
def atualizar_produto(produto_id):
    try:
        data = request.get_json()
        produto_data = ProdutoUpdate(
            codigo=data.get('codigo'),
            nome=data.get('nome'),
            tipo=data.get('tipo'),
            marca=data.get('marca'),
            unidade=data.get('unidade'),
            valor_unitario=Decimal(data['valor_unitario']) if 'valor_unitario' in data else None,
            estoque_quantidade=Decimal(data['estoque_quantidade']) if 'estoque_quantidade' in data else None
        )
        
        produto = update_produto(db.session, produto_id, produto_data)
        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso',
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'unidade': produto.unidade.value,
                'valor': str(produto.valor_unitario),
                'estoque': str(produto.estoque_quantidade)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@login_required
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
                'estoque_quantidade': str(produto.estoque_quantidade),
                'ativo': produto.ativo
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
@login_required
def remover_produto(produto_id):
    try:
        delete_produto(db.session, produto_id)
        return jsonify({'success': True, 'message': 'Produto removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/produtos/<int:produto_id>/movimentacao', methods=['POST'])
@login_required
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
            observacao=data.get('observacao')
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
def listar_usuarios():
    try:
        search = request.args.get('search', '').lower()
        usuarios = get_usuarios(db.session)
        
        result = []
        for usuario in usuarios:
            if search and (search not in usuario.nome.lower() and 
                          search not in usuario.email.lower()):
                continue
            if usuario.status == True:
                status = 'Ativo'
            else:
                status = 'Inativo'
                
            result.append({
                'id': usuario.id,
                'nome': usuario.nome,
                'tipo': usuario.tipo.value.capitalize(),
                'status': status,
                'ultimo_acesso': usuario.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if usuario.ultimo_acesso else 'Nunca',
                'cpf': usuario.cpf
            })
        
        return jsonify({'success': True, 'usuarios': result})
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
@login_required
def get_usuario(usuario_id):
    try:
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Verifica e formata os campos de forma segura
        ultimo_acesso = (
            usuario.ultimo_acesso.strftime('%d/%m/%Y %H:%M') 
            if hasattr(usuario, 'ultimo_acesso') and usuario.ultimo_acesso 
            else None
        )

        data_cadastro = (
            usuario.criado_em.strftime('%d/%m/%Y %H:%M')
            if hasattr(usuario, 'criado_em') and usuario.criado_em
            else None
        )

        
        response_data = {
            'success': True,
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome,
                'cpf': usuario.cpf,
                'tipo': usuario.tipo.value if hasattr(usuario.tipo, 'value') else str(usuario.tipo),
                'status': usuario.status.value if hasattr(usuario.status, 'value') else str(usuario.status),
                'ultimo_acesso': ultimo_acesso,
                'data_cadastro': data_cadastro,
                'observacoes': getattr(usuario, 'observacoes', None)
            }
        }
            
        return jsonify(response_data)
    except Exception as e:
        print(f"Error fetching user {usuario_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/usuarios', methods=['POST'])
@login_required
def criar_usuario():
    try:
        data = request.get_json()
        print("Recebido:", data)

        usuario_data = schemas.UsuarioCreate(**data)

        # Cria o usuário usando a função centralizada do CRUD
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
def atualizar_usuario(usuario_id):
    try:
        data = request.get_json()
        
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Atualiza nome e cpf
        if 'nome' in data:
            usuario.nome = data['nome']
        if 'cpf' in data:
            usuario.cpf = data['cpf']
        
        # Atualiza tipo - converte para enum TipoUsuario
        if 'tipo' in data:
            tipo_str = data['tipo'].lower()
            if tipo_str in entities.TipoUsuario.__members__:
                usuario.tipo = entities.TipoUsuario[tipo_str]
            else:
                return jsonify({'success': False, 'message': 'Tipo de usuário inválido'}), 400
        
        # Atualiza status (booleano)
        if 'status' in data:
            status_val = data['status']
            if isinstance(status_val, bool):
                usuario.status = status_val
            else:
                # Permitir strings 'ativo'/'inativo' (insensível)
                usuario.status = (str(status_val).lower() == 'ativo')
        
        # Atualiza observações se enviado
        if 'observacoes' in data:
            usuario.observacoes = data['observacoes']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso'})
    
    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@login_required
def remover_usuario(usuario_id):
    try:
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404

        db.session.delete(usuario)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuário removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ===== Financeiro Routes =====
@admin_bp.route('/financeiro', methods=['GET'])
@login_required
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