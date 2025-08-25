import csv
from functools import wraps
import io
import math
from zoneinfo import ZoneInfo
from flask import Blueprint, Response, app, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import traceback
from flask import send_file, make_response, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Table as PlatypusTable
)
from flask import make_response, request, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

from sqlalchemy import case, func
from sqlalchemy.orm import Session
from app import schemas
from app.models import db
from app.utils.format_data_moeda import format_currency, format_number
from app.models.entities import ( 
    Cliente, Produto, NotaFiscal, UnidadeMedida, StatusNota,
    Financeiro, TipoMovimentacao, CategoriaFinanceira, MovimentacaoEstoque, ContaReceber,
    StatusPagamento, Caixa, StatusCaixa, NotaFiscalItem, FormaPagamento, Entrega, TipoDesconto, PagamentoNotaFiscal,
    Desconto, PagamentoContaReceber)
from app.crud import (
    TipoEstoque, atualizar_desconto, buscar_desconto_by_id, buscar_descontos_por_produto_id, buscar_todos_os_descontos, calcular_fator_conversao,
    criar_desconto, deletar_desconto, get_caixa_aberto, abrir_caixa, fechar_caixa, get_caixas, get_caixa_by_id, 
    get_transferencias,get_user_by_cpf, get_user_by_id, get_usuarios, create_user, obter_caixas_completo,
    registrar_transferencia, update_user, get_produto, get_produtos, create_produto, update_produto, delete_produto,
    registrar_movimentacao, get_cliente, get_clientes, create_cliente, 
    update_cliente, delete_cliente, create_nota_fiscal, get_nota_fiscal, 
    get_notas_fiscais, create_lancamento_financeiro, get_lancamento_financeiro,
    get_lancamentos_financeiros, update_lancamento_financeiro, 
    delete_lancamento_financeiro, get_clientes_all, get_caixas_abertos
)
from app.schemas import (
    UsuarioCreate, UsuarioUpdate, ProdutoCreate, ProdutoUpdate, MovimentacaoEstoqueCreate,
    ClienteCreate, ClienteUpdate, FinanceiroCreate, FinanceiroUpdate
)
from app.utils.format_data_moeda import formatar_data_br, format_number
from app.utils.signature import SignatureLine

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

def to_decimal_2(value):
    """Converte para Decimal com no máximo 2 casas decimais"""
    if value is None:
        return None
    try:
        # Primeiro converte para string para evitar problemas com float
        str_value = str(value).strip()
        if not str_value:
            return None
        # Converte para Decimal e arredonda para 2 casas decimais
        decimal_value = Decimal(str_value).quantize(Decimal('0.01'))
        return decimal_value
    except (InvalidOperation, ValueError):
        return None

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
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1).date()

        # Métricas de Estoque (simplificado)
        estoque_metrics = db.session.query(
            Produto.unidade,
            func.sum(Produto.estoque_loja).label('total')
        ).filter(
            Produto.ativo == True
        ).group_by(Produto.unidade).all()

        estoque_dict = {
            'kg': 0,
            'saco': 0,
            'unidade': 0
        }
        
        for item in estoque_metrics:
            if item.unidade == UnidadeMedida.kg:
                estoque_dict['kg'] = item.total or 0
            elif item.unidade == UnidadeMedida.saco:
                estoque_dict['saco'] = item.total or 0
            elif item.unidade == UnidadeMedida.unidade:
                estoque_dict['unidade'] = item.total or 0

        # Métricas Financeiras (simplificado)
        entradas_mes = db.session.query(
            func.sum(Financeiro.valor)
        ).filter(
            Financeiro.tipo == TipoMovimentacao.entrada,
            Financeiro.data >= primeiro_dia_mes,
            Financeiro.data <= hoje
        ).scalar() or 0

        saidas_mes = db.session.query(
            func.sum(Financeiro.valor)
        ).filter(
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.data >= primeiro_dia_mes,
            Financeiro.data <= hoje,
            Financeiro.categoria != CategoriaFinanceira.fechamento_caixa
        ).scalar() or 0

        return jsonify({
            'success': True,
            'metrics': {
                'estoque': {
                    'kg': f"{format_number(estoque_dict['kg'], is_weight=True)} kg",
                    'sacos': f"{format_number(estoque_dict['saco'], is_weight=True)} sacos",
                    'unidades': f"{format_number(estoque_dict['unidade'], is_weight=True)} un"
                },
                'financeiro': {
                    'entradas_mes': format_currency(entradas_mes),
                    'saidas_mes': format_currency(saidas_mes),
                    'saldo_mes': format_currency(entradas_mes - saidas_mes)
                }
            }
        })

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/dashboard/vendas-diarias')
@login_required
@admin_required
def get_vendas_diarias():
    try:
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1).date()
        dados_diarios = []

        # 1. Vendas dos últimos 30 dias por caixa
        data_inicio_30_dias = hoje - timedelta(days=30)
        
        vendas_ultimos_30_dias = db.session.query(
            Caixa.id.label('caixa_id'),
            Caixa.data_abertura,
            func.sum(Financeiro.valor).label('total_vendas')
        ).join(
            Financeiro, Financeiro.caixa_id == Caixa.id
        ).filter(
            Financeiro.tipo == TipoMovimentacao.entrada,
            Financeiro.categoria == CategoriaFinanceira.venda,
            Financeiro.data >= data_inicio_30_dias,
            Financeiro.data <= hoje
        ).group_by(
            Caixa.id, Caixa.data_abertura
        ).order_by(
            Caixa.data_abertura.asc()
        ).all()

        # 2. Total de vendas no mês
        total_vendas_mes = db.session.query(
            func.sum(Financeiro.valor)
        ).filter(
            Financeiro.tipo == TipoMovimentacao.entrada,
            Financeiro.categoria == CategoriaFinanceira.venda,
            Financeiro.data >= primeiro_dia_mes,
            Financeiro.data <= hoje
        ).scalar() or 0

        # 3. Total de despesas no mês
        total_despesas_mes = db.session.query(
            func.sum(Financeiro.valor)
        ).filter(
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.categoria != CategoriaFinanceira.fechamento_caixa,
            Financeiro.data >= primeiro_dia_mes,
            Financeiro.data <= hoje
        ).scalar() or 0

        # 4. Dados diários (últimos 7 dias)
        for i in range(6, -1, -1):
            data = hoje - timedelta(days=i)
            
            # Total de vendas do dia
            total_vendas = db.session.query(
                func.sum(Financeiro.valor)
            ).filter(
                Financeiro.tipo == TipoMovimentacao.entrada,
                Financeiro.categoria == CategoriaFinanceira.venda,
                func.date(Financeiro.data) == data
            ).scalar() or 0

            # Total de despesas do dia
            total_despesas = db.session.query(
                func.sum(Financeiro.valor)
            ).filter(
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria != CategoriaFinanceira.fechamento_caixa,
                func.date(Financeiro.data) == data
            ).scalar() or 0

            # Formas de pagamento
            formas_pagamento = db.session.query(
                PagamentoNotaFiscal.forma_pagamento,
                func.sum(PagamentoNotaFiscal.valor).label('total')
            ).join(
                NotaFiscal, NotaFiscal.id == PagamentoNotaFiscal.nota_fiscal_id
            ).filter(
                func.date(NotaFiscal.data_emissao) == data,
                NotaFiscal.status == StatusNota.emitida
            ).group_by(
                PagamentoNotaFiscal.forma_pagamento
            ).all()

            dados_diarios.append({
                'data': data.strftime('%d/%m'),
                'total_vendas': format_currency(total_vendas),
                'total_despesas': format_currency(total_despesas),
                'saldo_dia': format_currency(total_vendas - total_despesas),
                'formas_pagamento': [
                    {'forma': fp.forma_pagamento.value, 'total': format_currency(fp.total or 0)}
                    for fp in formas_pagamento
                ]
            })

        return jsonify({
            'success': True,
            'dados': dados_diarios,
            'vendas_mensais_caixa': [
                {
                    #'caixa_id': caixa.caixa_id, 
                    'data_abertura': caixa.data_abertura.strftime('%d/%m/%Y'),
                    'total_vendas': format_currency(caixa.total_vendas or 0)
                }
                for caixa in vendas_ultimos_30_dias
            ],
            'resumo_mensal': {
                'total_vendas': format_currency(total_vendas_mes),
                'total_despesas': format_currency(total_despesas_mes),
                'saldo_mensal': format_currency(total_vendas_mes - total_despesas_mes)
            },
            'periodo': {
                'inicio': (hoje - timedelta(days=6)).strftime('%d/%m/%Y'),
                'fim': hoje.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/dashboard/vendas-mensais')
@login_required
@admin_required
def get_vendas_mensais():
    try:
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        meses = []
        vendas = []
        despesas = []
        
        # Obter dados dos últimos 6 meses
        for i in range(5, -1, -1):
            mes = hoje.month - i
            ano = hoje.year
            if mes <= 0:
                mes += 12
                ano -= 1
            
            primeiro_dia = datetime(ano, mes, 1).date()
            ultimo_dia = datetime(ano, mes + 1, 1).date() - timedelta(days=1) if mes < 12 else datetime(ano, 12, 31).date()
            
            # Vendas do mês
            total_vendas = db.session.query(
                func.sum(Financeiro.valor)
            ).filter(
                Financeiro.tipo == TipoMovimentacao.entrada,
                Financeiro.categoria == CategoriaFinanceira.venda,
                Financeiro.data >= primeiro_dia,
                Financeiro.data <= ultimo_dia
            ).scalar() or 0
            
            # Despesas do mês
            total_despesas = db.session.query(
                func.sum(Financeiro.valor)
            ).filter(
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria != CategoriaFinanceira.fechamento_caixa,
                Financeiro.data >= primeiro_dia,
                Financeiro.data <= ultimo_dia
            ).scalar() or 0
            
            meses.append(f"{primeiro_dia.strftime('%m/%Y')}")
            vendas.append(float(total_vendas))
            despesas.append(float(total_despesas))
        
        return jsonify({
            'success': True,
            'meses': meses,
            'vendas': vendas,
            'despesas': despesas
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/dashboard/movimentacoes')
@login_required
@admin_required
def get_movimentacoes():
    try:
        movimentacoes = db.session.query( MovimentacaoEstoque)\
            .order_by( MovimentacaoEstoque.data.desc())\
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
        caixa = get_caixas_abertos(db.session)
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

        # Validação e conversão de todos os campos numéricos
        update_fields = {}
        
        # Campos básicos
        for campo in ['codigo', 'nome', 'tipo', 'marca', 'unidade', 'ativo']:
            if campo in data:
                update_fields[campo] = data[campo]
        
        # Campos monetários (2 casas decimais)
        campos_monetarios = [
            'valor_unitario', 'valor_unitario_compra', 
            'valor_total_compra', 'imcs'
        ]
        for campo in campos_monetarios:
            if campo in data:
                valor = to_decimal_2(data[campo])
                if valor is None:
                    return jsonify({
                        'success': False,
                        'message': f'Valor inválido para {campo}'
                    }), 400
                update_fields[campo] = valor
        
        # Campos de estoque (3 casas decimais, mas vamos arredondar para 2)
        campos_estoque = [
            'estoque_loja', 'estoque_deposito', 'estoque_fabrica',
            'estoque_minimo', 'estoque_maximo'
        ]
        for campo in campos_estoque:
            if campo in data:
                try:
                    # Converte para Decimal com 3 casas e depois arredonda para 2
                    str_value = str(data[campo]).strip()
                    if not str_value:
                        continue
                    valor = Decimal(str_value).quantize(Decimal('0.001')).quantize(Decimal('0.01'))
                    update_fields[campo] = valor
                except (InvalidOperation, ValueError):
                    return jsonify({
                        'success': False,
                        'message': f'Valor de estoque inválido para {campo}'
                    }), 400
        
        # Campos de conversão de unidades
        for campo in ['peso_kg_por_saco', 'pacotes_por_saco', 'pacotes_por_fardo']:
            if campo in data:
                try:
                    if campo.startswith('peso'):
                        valor = Decimal(str(data[campo])).quantize(Decimal('0.001'))
                    else:
                        valor = int(data[campo])
                    update_fields[campo] = valor
                except (ValueError, InvalidOperation):
                    return jsonify({
                        'success': False,
                        'message': f'Valor inválido para {campo}'
                    }), 400

        # Criar objeto de atualização
        produto_data = ProdutoUpdate(**update_fields)
        
        # Atualizar o produto
        produto = update_produto(db.session, produto_id, produto_data)

        # Atualizar descontos (se fornecido)
        if 'descontos' in data or 'desconto_id' in data:
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

        # Formatar os valores para retorno
        produto_dict = {
            'id': produto.id,
            'nome': produto.nome,
            'valor_unitario': format_number(produto.valor_unitario),
            'estoque_loja': f"{float(produto.estoque_loja):.2f}",
            'descontos': [{
                'id': d.id,
                'identificador': d.identificador,
                'valor': format_number(d.valor),
                'quantidade_minima': f"{float(d.quantidade_minima):.2f}",
                'tipo': d.tipo.name
            } for d in produto.descontos]
        }

        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso',
            'produto': produto_dict
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar produto: {str(e)}'
        }), 400
        
        
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
        produto = db.session.query( Produto).get(produto_id)

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
            estoque_origem=data.get('estoque_origem',  TipoEstoque.loja),
            estoque_destino=data.get('estoque_destino',  TipoEstoque.loja)
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
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Content-Type deve ser application/json'}), 400

    try:
        dados_venda = request.get_json()
        print("Dados recebidos:", dados_venda)  # Log para depuração
        
        if dados_venda is None:
            return jsonify({'success': False, 'message': 'JSON inválido ou não enviado'}), 400

        # Função auxiliar para converter e validar decimais
        def validar_decimal(valor, campo, max_digits=12, decimal_places=2):
            try:
                if valor is None:
                    return None
                str_valor = str(valor).strip()
                if not str_valor:
                    return None
                decimal_val = Decimal(str_valor).quantize(Decimal('0.01'))
                if abs(decimal_val.as_tuple().exponent) > decimal_places:
                    raise ValueError(f"O campo {campo} deve ter no máximo {decimal_places} casas decimais")
                if len(str(decimal_val).replace('.', '').replace('-', '')) > max_digits:
                    raise ValueError(f"O campo {campo} deve ter no máximo {max_digits} dígitos no total")
                return decimal_val
            except (ValueError, InvalidOperation) as e:
                print(e)
                raise ValueError(f"Valor inválido para {campo}: {str(e)}")

        # Campos obrigatórios
        required_fields = ['cliente_id', 'itens', 'pagamentos', 'valor_total', 'caixa_id', 'data_emissao']
        for field in required_fields:
            if field not in dados_venda:
                return jsonify({'success': False, 'message': f'Campo obrigatório faltando: {field}'}), 400

        # Validar data de emissão
        try:
            data_emissao = datetime.strptime(dados_venda['data_emissao'], '%Y-%m-%d %H:%M:%S')
            if data_emissao > datetime.now():
                return jsonify({'success': False, 'message': 'Data de emissão não pode ser futura'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD HH:MM:SS'}), 400

        # Verificar caixa
        caixa =  Caixa.query.get(dados_venda['caixa_id'])
        if not caixa:
            return jsonify({'success': False, 'message': f'Caixa não encontrado: ID {dados_venda["caixa_id"]}'}), 404
        if caixa.status == 'aberto':
            return jsonify({'success': False, 'message': 'Para vendas retroativas, o caixa deve estar fechado'}), 400

        # Validar lista de itens
        if not isinstance(dados_venda['itens'], list) or len(dados_venda['itens']) == 0:
            return jsonify({'success': False, 'message': 'Lista de itens inválida ou vazia'}), 400

        # Validar lista de pagamentos
        if not isinstance(dados_venda['pagamentos'], list) or len(dados_venda['pagamentos']) == 0:
            return jsonify({'success': False, 'message': 'Lista de pagamentos inválida ou vazia'}), 400

        # Converter e validar valores principais
        try:
            cliente_id = int(dados_venda['cliente_id'])
            valor_total = validar_decimal(dados_venda['valor_total'], 'valor_total')
            total_descontos = validar_decimal(dados_venda.get('total_descontos', 0), 'total_descontos')
            
            # Validar cliente
            cliente =  Cliente.query.get(cliente_id)
            if not cliente:
                return jsonify({'success': False, 'message': f'Cliente não encontrado: ID {cliente_id}'}), 404
        except ValueError as e:
            print(e)
            return jsonify({'success': False, 'message': str(e)}), 400

        # Validar itens
        itens_validados = []
        for item in dados_venda['itens']:
            try:
                produto_id = int(item.get('produto_id'))
                produto =  Produto.query.get(produto_id)
                if not produto:
                    return jsonify({'success': False, 'message': f'Produto não encontrado: ID {produto_id}'}), 404

                quantidade = validar_decimal(item.get('quantidade'), 'quantidade', decimal_places=3)
                valor_unitario = validar_decimal(item.get('valor_unitario'), 'valor_unitario')
                valor_total_item = validar_decimal(item.get('valor_total'), 'valor_total')
                desconto_aplicado = validar_decimal(item.get('valor_desconto', 0), 'valor_desconto')

                if produto.estoque_loja < quantidade:
                    return jsonify({
                        'success': False,
                        'message': f'Estoque insuficiente para {produto.nome} (disponível: {produto.estoque_loja}, solicitado: {quantidade})'
                    }), 400

                itens_validados.append({
                    'produto': produto,
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario,
                    'valor_total': valor_total_item,
                    'desconto_aplicado': desconto_aplicado,
                    'tipo_desconto': item.get('desconto_info', {}).get('tipo')
                })
            except ValueError as e:
                return jsonify({'success': False, 'message': f'Erro no item: {str(e)}'}), 400

        # Validar pagamentos
        pagamentos_validados = []
        valor_a_prazo = Decimal('0.00')
        valor_a_vista = Decimal('0.00')
        
        for pagamento in dados_venda['pagamentos']:
            try:
                forma = pagamento.get('forma_pagamento')
                valor = validar_decimal(pagamento.get('valor'), 'valor_pagamento')
                
                if forma == 'a_prazo':
                    valor_a_prazo += valor
                else:
                    valor_a_vista += valor
                
                pagamentos_validados.append({
                    'forma': forma,
                    'valor': valor
                })
            except ValueError as e:
                return jsonify({'success': False, 'message': f'Erro no pagamento: {str(e)}'}), 400

        # Verificar soma dos pagamentos
        soma_pagamentos = valor_a_vista + valor_a_prazo
        if abs(soma_pagamentos - valor_total) > Decimal('0.01'):
            return jsonify({
                'success': False,
                'message': f'Valor recebido ({soma_pagamentos}) diferente do total da venda ({valor_total})'
            }), 400

        # Criar nota fiscal
        nota =  NotaFiscal(
            cliente_id=cliente.id,
            operador_id=current_user.id,
            caixa_id=caixa.id,
            data_emissao=data_emissao,
            valor_total=valor_total,
            valor_desconto=total_descontos,
            status= StatusNota.emitida,
            forma_pagamento= FormaPagamento.dinheiro,
            valor_recebido=valor_a_vista,
            troco=max(valor_a_vista - valor_total, Decimal('0.00')),
            a_prazo=valor_a_prazo > Decimal('0.00'),
            sincronizado=False
        )

        # Criar entrega se existir
        if 'endereco_entrega' in dados_venda and isinstance(dados_venda['endereco_entrega'], dict):
            entrega_data = dados_venda['endereco_entrega']
            entrega =  Entrega(
                logradouro=entrega_data.get('logradouro', ''),
                numero=entrega_data.get('numero', ''),
                complemento=entrega_data.get('complemento', ''),
                bairro=entrega_data.get('bairro', ''),
                cidade=entrega_data.get('cidade', ''),
                estado=entrega_data.get('estado', ''),
                cep=entrega_data.get('cep', ''),
                instrucoes=entrega_data.get('instrucoes', ''),
                sincronizado=False
            )
            db.session.add(entrega)
            db.session.flush()
            nota.entrega_id = entrega.id

        db.session.add(nota)
        db.session.flush()

        # Adicionar itens
        for item in itens_validados:
            item_nf =  NotaFiscalItem(
                nota_id=nota.id,
                produto_id=item['produto'].id,
                estoque_origem= TipoEstoque.loja,
                quantidade=item['quantidade'],
                valor_unitario=item['valor_unitario'],
                valor_total=item['valor_total'],
                desconto_aplicado=item['desconto_aplicado'],
                tipo_desconto= TipoDesconto(item['tipo_desconto']) if item['tipo_desconto'] else None,
                sincronizado=False
            )
            db.session.add(item_nf)
            item['produto'].estoque_loja -= item['quantidade']

        # Adicionar pagamentos
        pagamentos_ids = []
        for pagamento in pagamentos_validados:
            pagamento_nf =  PagamentoNotaFiscal(
                nota_fiscal_id=nota.id,
                forma_pagamento= FormaPagamento(pagamento['forma']),
                valor=pagamento['valor'],
                data=data_emissao,
                sincronizado=False
            )
            db.session.add(pagamento_nf)
            db.session.flush()
            pagamentos_ids.append(pagamento_nf.id)

            if pagamento['forma'] != 'a_prazo':
                financeiro =  Financeiro(
                    tipo= TipoMovimentacao.entrada,
                    categoria= CategoriaFinanceira.venda,
                    valor=pagamento['valor'],
                    descricao=f"Pagamento venda NF #{nota.id}",
                    cliente_id=cliente.id,
                    caixa_id=caixa.id,
                    nota_fiscal_id=nota.id,
                    pagamento_id=pagamento_nf.id,
                    data=data_emissao,
                    sincronizado=False
                )
                db.session.add(financeiro)

        # Criar conta a receber se houver valor a prazo
        if valor_a_prazo > Decimal('0.00'):
            conta_receber =  ContaReceber(
                cliente_id=cliente.id,
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo NF #{nota.id}",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=data_emissao + timedelta(days=30),
                status= StatusPagamento.pendente,
                sincronizado=False
            )
            db.session.add(conta_receber)

        # Definir forma de pagamento principal
        if len(pagamentos_validados) == 1:
            nota.forma_pagamento =  FormaPagamento(pagamentos_validados[0]['forma'])

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Venda retroativa registrada com sucesso',
            'nota_fiscal_id': nota.id,
            'valor_total': float(valor_total.quantize(Decimal('0.01'))),
            'valor_recebido': float(valor_a_vista.quantize(Decimal('0.01'))),
            'troco': float(nota.troco.quantize(Decimal('0.01'))) if nota.troco else 0,
            'valor_a_prazo': float(valor_a_prazo.quantize(Decimal('0.01'))) if valor_a_prazo > 0 else 0,
            'data_emissao': data_emissao.strftime('%Y-%m-%d %H:%M:%S')
        }), 201

    except SQLAlchemyError as e:
        print(e)
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro ao registrar venda retroativa no banco',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
        
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro inesperado ao registrar venda retroativa',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
        
# Rotas para carregar dados no modal
@admin_bp.route('/api/caixas/fechados', methods=['GET'])
@login_required
@admin_required
def api_caixas_fechados():
    try:
        caixas =  Caixa.query.filter_by(status='fechado').order_by( Caixa.data_fechamento.desc()).all()
        
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
        clientes =  Cliente.query.filter_by(ativo=True).order_by( Cliente.nome).all()
        
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
        produtos =  Produto.query.filter_by(ativo=True).order_by( Produto.nome).all()
        
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

        # Validar conversão se solicitada
        if converter_unidade:
            if not data.get('unidade_destino'):
                return jsonify({'success': False, 'message': 'Unidade de destino é obrigatória para conversão'}), 400
            if not data.get('quantidade_destino'):
                return jsonify({'success': False, 'message': 'Quantidade de destino é obrigatória para conversão'}), 400

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

        # Adicionar dados de conversão se aplicável
        if converter_unidade:
            transferencia_data['unidade_destino'] = data['unidade_destino']
            transferencia_data['quantidade_destino'] = Decimal(str(data['quantidade_destino']))

        transferencia = registrar_transferencia(db.session, transferencia_data)

        # Determinar nome do produto para resposta
        produto_nome = transferencia.produto.nome
        if transferencia.produto_destino_id and transferencia.produto_destino_id != transferencia.produto_id:
            produto_destino = db.session.query(Produto).get(transferencia.produto_destino_id)
            produto_nome = f"{produto_nome} → {produto_destino.nome} ({produto_destino.unidade.value})"

        return jsonify({
            'success': True,
            'message': 'Transferência realizada com sucesso',
            'transferencia': {
                'id': transferencia.id,
                'data': transferencia.data.strftime('%d/%m/%Y %H:%M'),
                'produto': produto_nome,
                'origem': transferencia.estoque_origem.value,
                'destino': transferencia.estoque_destino.value,
                'quantidade_origem': f"{transferencia.quantidade:.2f} {transferencia.unidade_origem}",
                'quantidade_destino': f"{transferencia.quantidade_destino:.2f} {transferencia.unidade_destino}" if transferencia.quantidade_destino else None,
                'usuario': transferencia.usuario.nome
            }
        })
    except Exception as e:
        db.session.rollback()
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

@admin_bp.route('/produtos/<int:produto_id>/calcular-conversao', methods=['POST'])
@login_required
@admin_required
def calcular_conversao(produto_id):
    try:
        data = request.get_json()
        quantidade = Decimal(str(data['quantidade']))
        unidade_origem = data['unidade_origem']
        unidade_destino = data['unidade_destino']
        fator_personalizado = Decimal(str(data.get('fator_personalizado', 0))) or None
        
        produto = db.session.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Calcular fator de conversão
        if fator_personalizado and fator_personalizado > 0:
            fator_conversao = fator_personalizado
        else:
            fator_conversao = calcular_fator_conversao(produto, unidade_origem, unidade_destino)
        
        quantidade_destino = quantidade * fator_conversao
        
        return jsonify({
            'success': True,
            'quantidade_destino': float(quantidade_destino),
            'fator_conversao': float(fator_conversao),
            'mensagem': f"1 {unidade_origem} = {fator_conversao} {unidade_destino}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

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
            'tipo':  TipoDesconto.fixo,  # Definindo como fixo para manter compatibilidade
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
        return jsonify({'success': False, 'erro': str(e)}), 500
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
        return jsonify({'success': False, 'erro': str(e)}), 500
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
        descontos = session.query( Desconto)\
            .order_by( Desconto.identificador)\
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
        return jsonify({'success': False, 'erro': str(e)}), 500
    finally:
        session.close()

@admin_bp.route('/descontos/<int:desconto_id>', methods=['GET'])
@login_required
def buscar_desconto_por_id(desconto_id):
    try:
        session = Session(db.engine)
        desconto = session.query( Desconto).get(desconto_id)
        
        if not desconto:
            return jsonify({'success': False, 'erro': 'Desconto não encontrado'}), 404
        
        valido_ate_formatado = desconto.valido_ate.strftime('%Y-%m-%d') if desconto.valido_ate else None
        
        return jsonify({
            'success': True,
            'desconto': {
                'id': desconto.id,
                'identificador': desconto.identificador,
                'quantidade_minima': float(desconto.quantidade_minima),
                'quantidade_maxima': float(desconto.quantidade_maxima),
                'valor_unitario_com_desconto': format_number(desconto.valor),  # Mapeando valor para valor_unitario_com_desconto
                'descricao': desconto.descricao,
                'valido_ate': valido_ate_formatado,
                'ativo': desconto.ativo,
                'criado_em': formatar_data_br(desconto.criado_em)
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'erro': str(e)}), 500
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
            return jsonify({'success': False, "error": "Dados não fornecidos"}), 400
            
        caixa = db.session.get( Caixa, caixa_id)
        if not caixa:
            return jsonify({'success': False, "error": "Caixa não encontrado"}), 404
        
        # Atualiza status e datas conforme ação
        if 'status' in dados:
            if dados['status'] == 'fechado':
                caixa.status =  StatusCaixa.fechado
                caixa.data_fechamento = datetime.now()
            elif dados['status'] == 'analise':
                caixa.status =  StatusCaixa.analise
                caixa.data_analise = datetime.now()
        
        if 'valor_fechamento' in dados:
            caixa.valor_fechamento = Decimal(dados['valor_fechamento'])
        if 'valor_abertura' in dados:
            caixa.valor_abertura = Decimal(dados['valor_abertura'])
            
        # Atualiza observações se existirem
        if 'observacoes_admin' in dados:
            caixa.observacoes_admin = dados['observacoes_admin']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
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
        return jsonify({'success': False, "error": f"Erro ao atualizar caixa: {str(e)}"}), 500

@admin_bp.route('/caixas/<int:caixa_id>', methods=['GET', 'PUT'])
@login_required
@admin_required
def caixa_detail(caixa_id):
    if request.method == 'GET':
        try:
            session = Session(db.engine)
            caixa = session.get( Caixa, caixa_id)
            
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
                
            caixa = db.session.get( Caixa, caixa_id)
            if not caixa:
                return jsonify({"success": False, "error": "Caixa não encontrado"}), 404
            
            # Atualiza status e datas conforme ação
            if 'status' in dados:
                if dados['status'] == 'fechado' and caixa.status !=  StatusCaixa.fechado:
                    caixa.status =  StatusCaixa.fechado
                    caixa.data_fechamento = datetime.now()
                elif dados['status'] == 'analise' and caixa.status !=  StatusCaixa.analise:
                    caixa.status =  StatusCaixa.analise
                    caixa.data_analise = datetime.now()
            
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
    session = Session(db.engine)
    try:
        # Busca informações do caixa
        caixa = session.query(Caixa).filter_by(id=caixa_id).first()
        if not caixa:
            return jsonify({'success': False, 'error': 'Caixa não encontrado'}), 404
            
        # Busca todas as movimentações financeiras do caixa
        movimentacoes = session.query(Financeiro)\
            .filter_by(caixa_id=caixa_id)\
            .order_by(Financeiro.data.desc())\
            .all()
        
        # Inicializa estruturas de dados
        dados = []
        totais_vendas = {
            'pix_fabiano': 0.0,
            'pix_maquineta': 0.0,
            'pix_edfrance': 0.0,
            'pix_loja': 0.0,
            'dinheiro': 0.0,
            'cartao_credito': 0.0,
            'cartao_debito': 0.0,
            'a_prazo': 0.0
        }

        # Processa cada movimentação
        for mov in movimentacoes:
            # Busca informações do cliente
            cliente_nome = None
            if mov.cliente_id:
                cliente = session.query(Cliente).get(mov.cliente_id)
                cliente_nome = cliente.nome if cliente else None
            
            # Busca formas de pagamento
            formas_pagamento = []
            if mov.nota_fiscal_id:
                pagamentos = session.query(PagamentoNotaFiscal)\
                    .filter_by(nota_fiscal_id=mov.nota_fiscal_id)\
                    .all()
                formas_pagamento = [p.forma_pagamento.value for p in pagamentos]
            
            if mov.conta_receber_id:
                pagamentos = session.query(PagamentoContaReceber)\
                    .filter_by(conta_id=mov.conta_receber_id)\
                    .all()
                formas_pagamento = [p.forma_pagamento.value for p in pagamentos]
                        
            # Adiciona ao array de dados
            dados.append({
                'id': mov.id,
                'data': mov.data.isoformat(),
                'tipo': mov.tipo.value,
                'categoria': mov.categoria.value if mov.categoria else None,
                'valor': float(mov.valor),
                'descricao': mov.descricao,
                'nota_fiscal_id': mov.nota_fiscal_id,
                'cliente_id': mov.cliente_id,
                'conta_receber_id': mov.conta_receber_id,
                'cliente_nome': cliente_nome,
                'formas_pagamento': formas_pagamento
            })

        # 1. CALCULA TOTAL DE ENTRADAS - SOMA TODAS AS FORMAS DE PAGAMENTO
        # Busca pagamentos de notas fiscais
        pagamentos_notas = session.query(
            PagamentoNotaFiscal.forma_pagamento,
            func.sum(PagamentoNotaFiscal.valor).label('total')
        ).join(
            NotaFiscal,
            PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id
        ).filter(
            NotaFiscal.caixa_id == caixa_id,
            NotaFiscal.status == StatusNota.emitida
        ).group_by(
            PagamentoNotaFiscal.forma_pagamento
        ).all()
        
        # Busca pagamentos de contas a receber
        pagamentos_contas = session.query(
            PagamentoContaReceber.forma_pagamento,
            func.sum(PagamentoContaReceber.valor_pago).label('total')
        ).filter(
            PagamentoContaReceber.caixa_id == caixa_id
        ).group_by(
            PagamentoContaReceber.forma_pagamento
        ).all()
        
        # Combina os resultados e calcula totais
        total_entradas = 0.0
        formas_pagamento = {}
        
        for forma, total in pagamentos_notas:
            valor = float(total)
            formas_pagamento[forma.value] = formas_pagamento.get(forma.value, 0) + valor
            total_entradas += valor
            
        for forma, total in pagamentos_contas:
            valor = float(total)
            formas_pagamento[forma.value] = formas_pagamento.get(forma.value, 0) + valor
            total_entradas += valor

        # 2. CALCULA TOTAL DE SAÍDAS - SOMENTE DESPESAS
        total_saidas = session.query(
            func.sum(Financeiro.valor)
        ).filter(
            Financeiro.caixa_id == caixa_id,
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.categoria == CategoriaFinanceira.despesa
        ).scalar() or 0.0
        
        total_saidas = float(total_saidas)

        # 3. CALCULA VALORES FÍSICOS E DIGITAIS
        valor_dinheiro = formas_pagamento.get('dinheiro', 0.0)
        valor_fisico = valor_dinheiro
        
        if caixa.valor_fechamento and caixa.valor_abertura:
            valor_abertura = float(caixa.valor_abertura)
            valor_fechamento = float(caixa.valor_fechamento)
            valor_fisico = max((valor_dinheiro + valor_abertura) - valor_fechamento - total_saidas, 0.0)

            # Pega parte inteira e parte decimal
            parte_inteira = math.floor(valor_fisico)
            parte_decimal = valor_fisico - parte_inteira

            if parte_decimal == 0.5:
                # Mantém o valor original (sem arredondar)
                valor_fisico = valor_fisico
            elif parte_decimal > 0.5:
                valor_fisico = math.ceil(valor_fisico)  # mais perto do de cima
            else:
                valor_fisico = math.floor(valor_fisico)  # mais perto do de baixo
            
        formas_pagamento['dinheiro'] = valor_fisico
        valor_digital = sum([
            formas_pagamento.get('pix_loja', 0.0),
            formas_pagamento.get('pix_fabiano', 0.0),
            formas_pagamento.get('pix_edfrance', 0.0),
            formas_pagamento.get('pix_maquineta', 0.0),
            formas_pagamento.get('cartao_debito', 0.0),
            formas_pagamento.get('cartao_credito', 0.0)
        ])

        a_prazo = formas_pagamento.get('a_prazo', 0.0)
        
        # 4. CALCULA TOTAL RECEBIDO DE CONTAS A PRAZO PARA ESTE CAIXA
        total_contas_prazo_recebidas = session.query(
            func.sum(PagamentoContaReceber.valor_pago)
        ).filter(
            PagamentoContaReceber.caixa_id == caixa_id
        ).scalar() or 0.0
        
        total_contas_prazo_recebidas = float(total_contas_prazo_recebidas)
        
        return jsonify({
            'success': True,
            'data': dados,
            'totais': {
                'entradas': total_entradas,
                'saidas': total_saidas,
                'saldo': total_entradas - total_saidas,
                'valor_fisico': valor_fisico,
                'valor_digital': valor_digital,
                'a_prazo': a_prazo,
                'contas_prazo_recebidas': total_contas_prazo_recebidas  # Novo campo adicionado
            },
            'vendas_por_forma_pagamento': formas_pagamento
        })
        
    except Exception as e:
        session.rollback()
        print(f"Erro no financeiro do caixa {caixa_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erro interno ao processar dados financeiros'
        }), 500
    finally:
        session.close()

@admin_bp.route('/caixas/<int:caixa_id>/financeiro/pdf')
@login_required
@admin_required
def gerar_pdf_caixa_financeiro(caixa_id):
    session = Session(db.engine)
    try:
        # --- Busca informações do caixa e operador ---
        caixa = session.query(Caixa).filter_by(id=caixa_id).first()
        if not caixa:
            raise Exception("Caixa não encontrado")
        operador_nome = caixa.operador.nome if caixa.operador else "Operador não identificado"
        caixa_data = caixa.data_fechamento if caixa.data_fechamento else caixa.data_abertura

        # --- BUSCA EXATAMENTE COMO NA API ---
        # Busca todas as movimentações financeiras do caixa
        movimentacoes = session.query(Financeiro)\
            .filter_by(caixa_id=caixa_id)\
            .order_by(Financeiro.data.desc())\
            .all()

        # --- CALCULA TOTAIS EXATAMENTE COMO NA API ---
        # 1. CALCULA TOTAL DE ENTRADAS - SOMA TODAS AS FORMAS DE PAGAMENTO
        # Busca pagamentos de notas fiscais (MESMO QUE NA API)
        pagamentos_notas = session.query(
            PagamentoNotaFiscal.forma_pagamento,
            func.sum(PagamentoNotaFiscal.valor).label('total')
        ).join(
            NotaFiscal,
            PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id
        ).filter(
            NotaFiscal.caixa_id == caixa_id,
            NotaFiscal.status == StatusNota.emitida
        ).group_by(
            PagamentoNotaFiscal.forma_pagamento
        ).all()
        
        # Busca pagamentos de contas a receber (MESMO QUE NA API)
        pagamentos_contas = session.query(
            PagamentoContaReceber.forma_pagamento,
            func.sum(PagamentoContaReceber.valor_pago).label('total')
        ).filter(
            PagamentoContaReceber.caixa_id == caixa_id
        ).group_by(
            PagamentoContaReceber.forma_pagamento
        ).all()
        
        # Combina os resultados e calcula totais (MESMO QUE NA API)
        total_entradas = 0.0
        formas_pagamento = {}
        
        for forma, total in pagamentos_notas:
            valor = float(total) if total else 0.0
            formas_pagamento[forma.value] = formas_pagamento.get(forma.value, 0) + valor
            total_entradas += valor
            
        for forma, total in pagamentos_contas:
            valor = float(total) if total else 0.0
            formas_pagamento[forma.value] = formas_pagamento.get(forma.value, 0) + valor
            total_entradas += valor

        # 2. CALCULA TOTAL DE SAÍDAS - SOMENTE DESPESAS (MESMO QUE NA API)
        total_saidas = session.query(
            func.sum(Financeiro.valor)
        ).filter(
            Financeiro.caixa_id == caixa_id,
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.categoria == CategoriaFinanceira.despesa
        ).scalar() or 0.0
        
        total_saidas = float(total_saidas)

        # 3. CALCULA VALORES FÍSICOS E DIGITAIS (MESMO QUE NA API)
        valor_dinheiro = formas_pagamento.get('dinheiro', 0.0)
        valor_fisico = valor_dinheiro
        
        if caixa.valor_fechamento and caixa.valor_abertura:
            valor_abertura = float(caixa.valor_abertura)
            valor_fechamento = float(caixa.valor_fechamento)
            valor_fisico = max((valor_dinheiro + valor_abertura) - valor_fechamento - total_saidas, 0.0)

            # Pega parte inteira e parte decimal (MESMO QUE NA API)
            parte_inteira = math.floor(valor_fisico)
            parte_decimal = valor_fisico - parte_inteira

            if parte_decimal == 0.5:
                # Mantém o valor original (sem arredondar)
                valor_fisico = valor_fisico
            elif parte_decimal > 0.5:
                valor_fisico = math.ceil(valor_fisico)  # mais perto do de cima
            else:
                valor_fisico = math.floor(valor_fisico)  # mais perto do de baixo
            
        formas_pagamento['dinheiro'] = valor_fisico
        valor_digital = sum([
            formas_pagamento.get('pix_loja', 0.0),
            formas_pagamento.get('pix_fabiano', 0.0),
            formas_pagamento.get('pix_edfrance', 0.0),
            formas_pagamento.get('pix_maquineta', 0.0),
            formas_pagamento.get('cartao_debito', 0.0),
            formas_pagamento.get('cartao_credito', 0.0)
        ])

        a_prazo = formas_pagamento.get('a_prazo', 0.0)
        
        # 4. CALCULA TOTAL RECEBIDO DE CONTAS A PRAZO (MESMO QUE NA API)
        total_contas_prazo_recebidas = session.query(
            func.sum(PagamentoContaReceber.valor_pago)
        ).filter(
            PagamentoContaReceber.caixa_id == caixa_id
        ).scalar() or 0.0
        
        total_contas_prazo_recebidas = float(total_contas_prazo_recebidas)

        # --- Configuração para bobina 80mm ---
        bobina_width = 226
        bobina_height = 3000
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(bobina_width, bobina_height),
            leftMargin=5,
            rightMargin=5,
            topMargin=-6,
            bottomMargin=5
        )
        elements = []

        # --- Estilos ---
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            name='Header',
            parent=styles['Heading1'],
            fontSize=14,
            leading=14,
            alignment=1,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=12,
            leading=12,
            alignment=1,
            fontName='Helvetica-Bold',
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=10,
            leading=10,
            alignment=0,
            fontName='Helvetica'
        )
        valor_style = ParagraphStyle(
            name='Valor',
            parent=normal_style,
            alignment=2,
            fontName='Helvetica-Bold'
        )
        linha_style = ParagraphStyle(
            name='Linha',
            parent=normal_style,
            alignment=1,
            textColor=colors.black
        )

        def moeda_br(valor):
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        def linha_separadora():
            return Paragraph("=" * 34, linha_style)

        # Função para criar linha alinhada com tabela invisível
        from reportlab.platypus import Table, TableStyle
        def linha_dupla(label, valor):
            tabela = Table(
                [[Paragraph(label, normal_style), Paragraph(valor, valor_style)]],
                colWidths=[120, 80]
            )
            tabela.setStyle(TableStyle([
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (0,0), 'Helvetica'),
                ('FONTNAME', (1,0), (1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            return tabela

        # --- Logo ---
        from flask import current_app
        import os
        from PIL import Image as PILImage
        from reportlab.platypus import Image, Spacer
        logo_path = os.path.join(current_app.root_path, 'static', 'assets', 'logo.jpeg')
        if os.path.exists(logo_path):
            try:
                with PILImage.open(logo_path) as img:
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                logo_width = 250
                logo_height = logo_width / aspect_ratio
                logo = Image(logo_path, width=logo_width, height=logo_height)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(0, 6))
            except Exception as e:
                print(f"Erro ao carregar a logo: {e}")

        # --- Cabeçalho ---
        elements.append(Paragraph("RELATÓRIO FINANCEIRO", header_style))
        elements.append(linha_separadora())
        elements.append(Spacer(1, 6))
        data_relatorio = caixa_data.strftime("%d/%m/%Y %H:%M") if caixa_data else "Data não disponível"
        elements.append(Paragraph(f"Data: {data_relatorio}", normal_style))
        elements.append(Paragraph(f"Operador: {operador_nome}", normal_style))
        elements.append(Spacer(1, 6))

        # --- Resumo Financeiro ---
        elements.append(linha_separadora())
        elements.append(Paragraph("RESUMO FINANCEIRO", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())
        elements.append(linha_dupla("Total Entradas:", moeda_br(total_entradas)))
        elements.append(linha_dupla("Total Saídas:", moeda_br(total_saidas)))
        elements.append(linha_dupla("Saldo:", moeda_br(total_entradas - total_saidas)))
        elements.append(Spacer(1, 6))
        elements.append(linha_dupla("Valor Físico:", moeda_br(valor_fisico)))
        elements.append(linha_dupla("Valor Digital:", moeda_br(valor_digital)))
        elements.append(linha_dupla("A Prazo:", moeda_br(a_prazo)))
        elements.append(linha_dupla("A Prazo Recebidos:", moeda_br(total_contas_prazo_recebidas)))
        
        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())
        elements.append(Spacer(1, 1))
        elements.append(Paragraph("Valores do Caixa", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(linha_separadora())
        
        # Adiciona valores de abertura e fechamento apenas se existirem
        valor_abertura = float(caixa.valor_abertura) if caixa.valor_abertura else 0.0
        valor_fechamento = float(caixa.valor_fechamento) if caixa.valor_fechamento else 0.0
        
        elements.append(linha_dupla("Abertura:", moeda_br(valor_abertura)))
        elements.append(linha_dupla("Fechamento:", moeda_br(valor_fechamento)))
        
        # --- Vendas por Forma de Pagamento ---
        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())
        elements.append(Spacer(1, 1))
        elements.append(Paragraph("FORMAS DE PAGAMENTO", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(linha_separadora())
        
        nomes_formas = {
            'dinheiro': 'Dinheiro',
            'pix_loja': 'PIX Loja',
            'pix_fabiano': 'PIX Fabiano',
            'pix_edfrance': 'PIX Edfranci',
            'pix_maquineta': 'PIX Maquineta',
            'cartao_debito': 'Cartão Débito',
            'cartao_credito': 'Cartão Crédito',
            'a_prazo': 'A Prazo'
        }
        
        # Exibe todas as formas de pagamento que têm valor
        for forma, valor in formas_pagamento.items():
            if valor > 0:
                nome_forma = nomes_formas.get(forma, forma)
                elements.append(linha_dupla(f"{nome_forma}:", moeda_br(valor)))
        # --- Movimentações Financeiras ---
        elements.append(Spacer(1, 8))
        elements.append(linha_separadora())
        elements.append(Paragraph("MOVIMENTAÇÕES", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(linha_separadora())
        for mov in movimentacoes:
            tipo_cat = f"{mov.tipo.value}"
            if mov.categoria:
                tipo_cat += f" - {mov.categoria.value}"
            elements.append(linha_dupla(tipo_cat, moeda_br(float(mov.valor))))
            if mov.descricao:
                descricao = mov.descricao
                if len(descricao) > 25:
                    words = descricao
                    lines = []
                    current_line = ""
                    for word in words:
                        if len(current_line + word) > 25:
                            lines.append(current_line)
                            current_line = word + ""
                        else:
                            current_line += word + ""
                    if current_line:
                        lines.append(current_line)
                    for line in lines:
                        elements.append(Paragraph(line, normal_style))
                else:
                    elements.append(Paragraph(descricao, normal_style))
            elements.append(linha_separadora())
        
        # --- Assinaturas ---
        elements.append(Spacer(1, 15))
        elements.append(linha_separadora())
        elements.append(Paragraph("ASSINATURAS", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(linha_separadora())
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Operador:", normal_style))
        elements.append(Paragraph("____________________________________", normal_style))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Administrador:", normal_style))
        elements.append(Paragraph("____________________________________", normal_style))

        doc.build(elements)
        buffer.seek(0)

        response = make_response(send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"caixa_{caixa_id}_bobina.pdf"
        ))
        response.headers['Content-Disposition'] = f'inline; filename=caixa_{caixa_id}_bobina.pdf'
        return response

    except Exception as e:
        session.rollback()
        print(f"Erro ao gerar PDF do caixa {caixa_id}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@admin_bp.route('/caixas/<int:caixa_id>/aprovar', methods=['POST'])
@login_required
@admin_required
def aprovar_caixa(caixa_id):
    """Rota para aprovar o fechamento de um caixa"""
    caixa =  Caixa.query.get_or_404(caixa_id)
    
    if current_user.tipo != 'admin':
        return jsonify({'success': False, 'error': 'Apenas administradores podem aprovar caixas'}), 403
    
    data = request.get_json()
    valor_confirmado = data.get('valor_confirmado')
    observacoes = data.get('observacoes')
    print(data)
    try:
        caixa.aprovar_fechamento(
            administrador_id=current_user.id,
            valor_confirmado=valor_confirmado,
            observacoes_admin=observacoes
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Caixa aprovado com sucesso',
            'status': caixa.status.value,
            'valor_confirmado': float(caixa.valor_confirmado) if caixa.valor_confirmado else None
        }), 200
    except ValueError as e:
        print(e)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Erro ao aprovar caixa: {str(e)}'}), 500

@admin_bp.route('/caixas/<int:caixa_id>/recusar', methods=['POST'])
@login_required
@admin_required
def recusar_caixa(caixa_id):
    """Rota para recusar o fechamento de um caixa"""
    caixa =  Caixa.query.get_or_404(caixa_id)
    
    if current_user.tipo != 'admin':
        return jsonify({'success': False, 'error': 'Apenas administradores podem recusar caixas'}), 403
    
    data = request.get_json()
    motivo = data.get('motivo')
    valor_correto = data.get('valor_correto')
    
    if not motivo:
        return jsonify({'success': False, 'error': 'Motivo da recusa é obrigatório'}), 400
    
    try:
        caixa.rejeitar_fechamento(
            administrador_id=current_user.id,
            motivo=motivo,
            valor_correto=valor_correto
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Caixa recusado com sucesso',
            'status': caixa.status.value,
            'observacoes_admin': caixa.observacoes_admin
        }), 200
    except ValueError as e:
        print(e)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Erro ao recusar caixa: {str(e)}'}), 500

@admin_bp.route('/caixas/<int:caixa_id>/enviar_analise', methods=['POST'])
@login_required
@admin_required
def enviar_para_analise(caixa_id):
    """Rota para enviar um caixa para análise (fechamento inicial)"""
    print(f"Recebendo solicitação para caixa {caixa_id}")  # Log de depuração
    
    try:
        caixa =  Caixa.query.get_or_404(caixa_id)
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
            'success': True,
            'message': 'Caixa enviado para análise com sucesso',
            'status': caixa.status.value,
            'valor_fechamento': float(caixa.valor_fechamento)
        }), 200
        
    except ValueError as e:
        print(f"Erro de valor: {str(e)}")  # Log de depuração
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro interno: {str(e)}")  # Log de depuração
        return jsonify({'success': False, 'error': f'Erro ao enviar caixa para análise: {str(e)}'}), 500

@admin_bp.route('/caixas/<int:caixa_id>/reabrir', methods=['POST'])
@login_required
@admin_required
def reabrir_caixa(caixa_id):
    """Rota para reabrir um caixa fechado ou recusado"""
    caixa =  Caixa.query.get_or_404(caixa_id)
    
    if current_user.tipo != 'admin':
        return jsonify({'success': False, 'error': 'Apenas administradores podem reabrir caixas'}), 403
    
    data = request.get_json()
    motivo = data.get('motivo')
    
    try:
        caixa.reabrir_caixa(
            administrador_id=current_user.id,
            motivo=motivo
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Caixa reaberto com sucesso',
            'status': caixa.status.value
        }), 200
    except ValueError as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Erro ao reabrir caixa: {str(e)}'}), 500
    
# =============== RELATÓRIO DE SAIDA DE PRODUTOS ======================
from flask import jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from zoneinfo import ZoneInfo

@admin_bp.route('/relatorios/vendas-produtos', methods=['GET'])
@login_required
@admin_required
def relatorio_vendas_produtos():
    try:
        # Obter parâmetros de filtro da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        produto_nome = request.args.get('produto_nome')
        produto_codigo = request.args.get('produto_codigo')
        categoria = request.args.get('categoria')
        limite = request.args.get('limite', default=50, type=int)
        
        # Definir datas padrão (últimos 30 dias) se não fornecidas
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        if not data_inicio:
            data_inicio = (hoje - timedelta(days=30)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = hoje.strftime('%Y-%m-%d')
        
        # Converter strings para objetos date
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Construir a query base para produtos vendidos
        query = db.session.query(
            Produto.id.label('produto_id'),
            Produto.nome.label('produto_nome'),
            Produto.codigo.label('produto_codigo'),
            Produto.unidade.label('unidade'),
            func.sum(NotaFiscalItem.quantidade).label('quantidade_vendida'),
            func.sum(NotaFiscalItem.valor_total).label('valor_total_vendido'),
            func.sum(NotaFiscalItem.quantidade * Produto.valor_unitario_compra).label('custo_total'),
            Produto.estoque_loja.label('estoque_atual_loja'),
            Produto.estoque_minimo.label('estoque_minimo')
        ).join(
            NotaFiscalItem,
            NotaFiscalItem.produto_id == Produto.id
        ).join(
            NotaFiscal,
            NotaFiscal.id == NotaFiscalItem.nota_id
        ).filter(
            NotaFiscal.status == StatusNota.emitida,
            NotaFiscal.data_emissao >= data_inicio,
            NotaFiscal.data_emissao <= data_fim + timedelta(days=1)  # Inclui todo o dia final
        ).group_by(
            Produto.id
        ).order_by(
            func.sum(NotaFiscalItem.quantidade).desc()
        )
        
        # Aplicar filtros adicionais
        if produto_nome:
            query = query.filter(Produto.nome.ilike(f'%{produto_nome}%'))
        
        if produto_codigo:
            query = query.filter(Produto.codigo.ilike(f'%{produto_codigo}%'))
        
        if categoria:
            query = query.filter(Produto.tipo == categoria)
        
        # Limitar resultados se necessário
        if limite:
            query = query.limit(limite)
        
        # Executar a query
        resultados = query.all()
        
        # Calcular despesas e estornos no período
        despesas_query = db.session.query(
            func.sum(Financeiro.valor).label('total_despesas')
        ).filter(
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.categoria == CategoriaFinanceira.despesa,
            Financeiro.data >= data_inicio,
            Financeiro.data <= data_fim + timedelta(days=1)
        ).first()
        
        estornos_query = db.session.query(
            func.sum(Financeiro.valor).label('total_estornos')
        ).filter(
            Financeiro.tipo == TipoMovimentacao.saida_estorno,
            Financeiro.data >= data_inicio,
            Financeiro.data <= data_fim + timedelta(days=1)
        ).first()
        
        total_despesas = despesas_query.total_despesas or 0
        total_estornos = estornos_query.total_estornos or 0
        
        # Processar os resultados para o relatório
        relatorio = []
        lucro_bruto_total = 0
        
        for r in resultados:
            # Calcular lucro bruto para este produto
            custo_total = float(r.custo_total) if r.custo_total else 0
            valor_total_vendido = float(r.valor_total_vendido)
            lucro_bruto = valor_total_vendido - custo_total
            
            lucro_bruto_total += lucro_bruto
            
            # Calcular percentual de estoque atual em relação ao mínimo
            percentual_estoque = 0
            if r.estoque_minimo > 0:
                percentual_estoque = (r.estoque_atual_loja / r.estoque_minimo) * 100
            
            relatorio.append({
                'produto_id': r.produto_id,
                'produto_nome': r.produto_nome,
                'produto_codigo': r.produto_codigo,
                'unidade': r.unidade.value,
                'quantidade_vendida': float(r.quantidade_vendida),
                'valor_total_vendido': valor_total_vendido,
                'custo_total': custo_total,
                'lucro_bruto': lucro_bruto,
                'margem_lucro': (lucro_bruto / valor_total_vendido * 100) if valor_total_vendido > 0 else 0,
                'estoque_atual_loja': float(r.estoque_atual_loja),
                'estoque_minimo': float(r.estoque_minimo),
                'percentual_estoque': round(percentual_estoque, 2),
                'status_estoque': 'CRÍTICO' if r.estoque_atual_loja < r.estoque_minimo else 'OK',
                'dias_restantes': (
                    round(r.estoque_atual_loja / (r.quantidade_vendida / 30), 2)
                    if r.quantidade_vendida > 0 else None
                )
            })
        
        # Calcular lucro líquido total
        lucro_liquido_total = lucro_bruto_total - float(total_despesas) - float(total_estornos)
        
        # Adicionar totais ao relatório
        total_vendido = sum(item['valor_total_vendido'] for item in relatorio)
        total_quantidade = sum(item['quantidade_vendida'] for item in relatorio)
        total_custo = sum(item['custo_total'] for item in relatorio)
        
        meta_relatorio = {
            'data_inicio': data_inicio.strftime('%Y-%m-%d'),
            'data_fim': data_fim.strftime('%Y-%m-%d'),
            'total_produtos': len(relatorio),
            'total_quantidade_vendida': total_quantidade,
            'total_valor_vendido': total_vendido,
            'total_custo': total_custo,
            'lucro_bruto': lucro_bruto_total,
            'lucro_liquido': lucro_liquido_total,
            'produtos_estoque_critico': sum(1 for item in relatorio if item['status_estoque'] == 'CRÍTICO')
        }
        
        return jsonify({
            'meta': meta_relatorio,
            'dados': relatorio
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/relatorios/vendas-diarias', methods=['GET'])
@login_required
@admin_required
def relatorio_vendas_diarias():
    try:
        # Obter parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        agrupar_por = request.args.get('agrupar_por', default='dia')  # 'dia', 'semana', 'mes'
        
        # Definir datas padrão (últimos 30 dias)
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        if not data_inicio:
            data_inicio = (hoje - timedelta(days=30)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = hoje.strftime('%Y-%m-%d')
        
        # Converter strings para objetos date
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Definir a expressão de agrupamento baseada no parâmetro
        if agrupar_por == 'dia':
            group_expr = func.date(NotaFiscal.data_emissao)
            label_format = '%Y-%m-%d'
        elif agrupar_por == 'semana':
            group_expr = func.date_trunc('week', NotaFiscal.data_emissao)
            label_format = 'Semana %Y-%m-%d'
        elif agrupar_por == 'mes':
            group_expr = func.date_trunc('month', NotaFiscal.data_emissao)
            label_format = '%Y-%m'
        else:
            return jsonify({'error': 'Agrupamento inválido. Use dia, semana ou mes'}), 400
        
        # Query para obter vendas agrupadas por período
        vendas_por_periodo = db.session.query(
            group_expr.label('periodo'),
            func.count(NotaFiscal.id).label('quantidade_vendas'),
            func.sum(NotaFiscal.valor_total).label('valor_total'),
            func.sum(NotaFiscal.valor_desconto).label('valor_desconto_total')
        ).filter(
            NotaFiscal.status == StatusNota.emitida,
            NotaFiscal.data_emissao >= data_inicio,
            NotaFiscal.data_emissao <= data_fim + timedelta(days=1)
        ).group_by(
            group_expr
        ).order_by(
            group_expr
        ).all()
        
        # Query para obter produtos mais vendidos no período
        produtos_mais_vendidos = db.session.query(
            Produto.id,
            Produto.nome,
            func.sum(NotaFiscalItem.quantidade).label('quantidade_total'),
            func.sum(NotaFiscalItem.valor_total).label('valor_total')
        ).join(
            NotaFiscalItem,
            NotaFiscalItem.produto_id == Produto.id
        ).join(
            NotaFiscal,
            NotaFiscal.id == NotaFiscalItem.nota_id
        ).filter(
            NotaFiscal.status == StatusNota.emitida,
            NotaFiscal.data_emissao >= data_inicio,
            NotaFiscal.data_emissao <= data_fim + timedelta(days=1)
        ).group_by(
            Produto.id
        ).order_by(
            func.sum(NotaFiscalItem.quantidade).desc()
        ).limit(5).all()
        
        # Processar resultados
        relatorio_periodo = [{
            'periodo': r.periodo.strftime(label_format),
            'quantidade_vendas': r.quantidade_vendas,
            'valor_total': float(r.valor_total),
            'valor_desconto_total': float(r.valor_desconto_total),
            'valor_liquido': float(r.valor_total - r.valor_desconto_total)
        } for r in vendas_por_periodo]
        
        relatorio_produtos = [{
            'produto_id': r.id,
            'produto_nome': r.nome,
            'quantidade_total': float(r.quantidade_total),
            'valor_total': float(r.valor_total)
        } for r in produtos_mais_vendidos]
        
        return jsonify({
            'meta': {
                'data_inicio': data_inicio.strftime('%Y-%m-%d'),
                'data_fim': data_fim.strftime('%Y-%m-%d'),
                'agrupar_por': agrupar_por
            },
            'vendas_por_periodo': relatorio_periodo,
            'produtos_mais_vendidos': relatorio_produtos
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/relatorios/vendas-produtos/exportar', methods=['GET'])
@login_required
@admin_required
def exportar_relatorio_vendas_produtos():
    try:
        # Os mesmos parâmetros da rota /relatorios/vendas-produtos
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        produto_id = request.args.get('produto_id')
        categoria = request.args.get('categoria')
        limite = request.args.get('limite', default=50, type=int)
        
        # Chame a função existente para obter os dados
        relatorio = relatorio_vendas_produtos().get_json()
        
        # Crie um arquivo CSV ou Excel (exemplo simplificado)
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escreva o cabeçalho
        writer.writerow([
            'ID Produto', 'Nome Produto', 'Unidade', 
            'Quantidade Vendida', 'Valor Total Vendido',
            'Estoque Atual Loja', 'Estoque Mínimo', 
            'Status Estoque', 'Dias Restantes'
        ])
        
        # Escreva os dados
        for item in relatorio['dados']:
            writer.writerow([
                item['produto_id'],
                item['produto_nome'],
                item['unidade'],
                item['quantidade_vendida'],
                item['valor_total_vendido'],
                item['estoque_atual_loja'],
                item['estoque_minimo'],
                item['status_estoque'],
                item['dias_restantes'] or ''
            ])
        
        # Retorne o arquivo para download
        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=relatorio_saidas_produtos.csv"}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/api/produtos/categorias', methods=['GET'])
@login_required
@admin_required
def get_produto_categorias():
    try:
        # Query distinct product categories from the database
        categorias = db.session.query(Produto.tipo).distinct().all()
        
        # Extract just the category names from the query results
        categorias_list = [categoria[0] for categoria in categorias if categoria[0]]
        
        return jsonify({
            'categorias': sorted(categorias_list)  # Return sorted list of categories
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/relatorios/vendas-produtos/detalhes', methods=['GET'])
@login_required
@admin_required
def relatorio_vendas_produtos_detalhes():
    try:
        # Obter parâmetros de filtro
        produto_id = request.args.get('produto_id')
        produto_nome = request.args.get('produto_nome')
        produto_codigo = request.args.get('produto_codigo')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Validação básica dos parâmetros
        if not any([produto_id, produto_nome, produto_codigo]):
            return jsonify({
                'success': False, 
                'message': 'É necessário fornecer pelo menos um filtro (ID, nome ou código do produto)'
            }), 400
        
        # Conversão de datas com tratamento de erros
        data_inicio_obj = None
        data_fim_obj = None
        try:
            if data_inicio and data_inicio.lower() != 'undefined':
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if data_fim and data_fim.lower() != 'undefined':
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Converter para datetime para filtros
        data_inicio_dt = datetime.combine(data_inicio_obj, datetime.min.time()) if data_inicio_obj else None
        data_fim_dt = datetime.combine(data_fim_obj, datetime.max.time()) if data_fim_obj else None
        
        # Construir query base
        produto_query = db.session.query(
            Produto.id.label('produto_id'),
            Produto.nome.label('produto_nome'),
            Produto.codigo.label('produto_codigo'),
            Produto.tipo.label('produto_tipo'),
            Produto.unidade.label('unidade'),
            func.sum(NotaFiscalItem.quantidade).label('quantidade_vendida'),
            func.sum(NotaFiscalItem.valor_total).label('valor_total_vendido'),
            Produto.estoque_loja.label('estoque_atual_loja'),
            Produto.estoque_minimo.label('estoque_minimo')
        ).join(
            NotaFiscalItem,
            NotaFiscalItem.produto_id == Produto.id
        ).join(
            NotaFiscal,
            NotaFiscal.id == NotaFiscalItem.nota_id
        ).filter(
            NotaFiscal.status == StatusNota.emitida
        )
        
        # Aplicar filtros do produto
        if produto_id:
            produto_query = produto_query.filter(Produto.id == produto_id)
        if produto_nome:
            produto_query = produto_query.filter(Produto.nome.ilike(f'%{produto_nome}%'))
        if produto_codigo:
            produto_query = produto_query.filter(Produto.codigo.ilike(f'%{produto_codigo}%'))
        
        # Aplicar filtros de data
        if data_inicio_dt:
            produto_query = produto_query.filter(NotaFiscal.data_emissao >= data_inicio_dt)
        if data_fim_dt:
            produto_query = produto_query.filter(NotaFiscal.data_emissao <= data_fim_dt)
        
        # Executar query
        produto_info = produto_query.group_by(Produto.id).first()
        
        if not produto_info:
            return jsonify({'success': False, 'message': 'Nenhum produto encontrado com os filtros fornecidos'}), 404
        
        # Calcular métricas adicionais
        status_estoque = 'CRÍTICO' if produto_info.estoque_atual_loja < produto_info.estoque_minimo else 'OK'
        
        dias_restantes = None
        if produto_info.quantidade_vendida and produto_info.quantidade_vendida > 0:
            periodo_dias = 30  # Período padrão para cálculo
            if data_inicio_obj and data_fim_obj:
                periodo_dias = (data_fim_obj - data_inicio_obj).days or 30
            media_diaria = produto_info.quantidade_vendida / periodo_dias
            dias_restantes = round(produto_info.estoque_atual_loja / media_diaria, 2) if media_diaria > 0 else None
        
        # Obter histórico detalhado de vendas
        historico_query = db.session.query(
            NotaFiscal.data_emissao,
            NotaFiscalItem.quantidade,
            NotaFiscalItem.valor_unitario,
            NotaFiscalItem.valor_total,
            Cliente.nome.label('cliente_nome')
        ).join(
            NotaFiscal,
            NotaFiscal.id == NotaFiscalItem.nota_id
        ).outerjoin(
            Cliente,
            Cliente.id == NotaFiscal.cliente_id
        ).filter(
            NotaFiscalItem.produto_id == produto_info.produto_id,
            NotaFiscal.status == StatusNota.emitida
        )
        
        # Aplicar filtros de data no histórico
        if data_inicio_dt:
            historico_query = historico_query.filter(NotaFiscal.data_emissao >= data_inicio_dt)
        if data_fim_dt:
            historico_query = historico_query.filter(NotaFiscal.data_emissao <= data_fim_dt)
        
        historico = historico_query.order_by(NotaFiscal.data_emissao.desc()).limit(50).all()
        
        # Formatar resposta
        return jsonify({
            'success': True,
            'produto': {
                'produto_id': produto_info.produto_id,
                'produto_nome': produto_info.produto_nome,
                'produto_codigo': produto_info.produto_codigo,
                'produto_tipo': produto_info.produto_tipo,
                'unidade': produto_info.unidade.value,
                'quantidade_vendida': float(produto_info.quantidade_vendida),
                'valor_total_vendido': float(produto_info.valor_total_vendido),
                'estoque_atual_loja': float(produto_info.estoque_atual_loja),
                'estoque_minimo': float(produto_info.estoque_minimo),
                'status_estoque': status_estoque,
                'dias_restantes': dias_restantes
            },
            'historico': [{
                'data_emissao': item.data_emissao.isoformat(),
                'quantidade': float(item.quantidade),
                'valor_unitario': float(item.valor_unitario),
                'valor_total': float(item.valor_total),
                'cliente_nome': item.cliente_nome
            } for item in historico]
        })
        
    except Exception as e:
        print(f"Erro no relatório de vendas detalhado: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro interno no servidor'}), 500


@admin_bp.route('/relatorios/vendas-produtos/pdf', methods=['GET'])
@login_required
@admin_required
def relatorio_vendas_produtos_pdf():
    try:
        # Obter os dados
        relatorio_data = relatorio_vendas_produtos().get_json()
        if 'error' in relatorio_data:
            return jsonify(relatorio_data), 500
        
        data_inicio = datetime.strptime(relatorio_data['meta']['data_inicio'], "%Y-%m-%d")
        data_fim = datetime.strptime(relatorio_data['meta']['data_fim'], "%Y-%m-%d")

        # Formatar para DD/MM/YYYY
        data_inicio_fmt = data_inicio.strftime("%d/%m/%Y")
        data_fim_fmt = data_fim.strftime("%d/%m/%Y")

        # Criar buffer para o PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              leftMargin=15*mm, rightMargin=15*mm,
                              topMargin=20*mm, bottomMargin=20*mm)
        
        styles = getSampleStyleSheet()
        elements = []
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        normal_style = styles['Normal']
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold'
        )
        
        # Título
        elements.append(Paragraph('Relatório de Vendas de Produtos', title_style))
        
        # Informações do relatório
        elements.append(Paragraph(f"Período: {data_inicio_fmt} a {data_fim_fmt}", subtitle_style))
        elements.append(Paragraph(f"Total de produtos: {relatorio_data['meta']['total_produtos']}", subtitle_style))
        elements.append(Paragraph(f"Quantidade total vendida: {relatorio_data['meta']['total_quantidade_vendida']}", subtitle_style))
        elements.append(Paragraph(f"Valor total vendido: {formatarMoeda(relatorio_data['meta']['total_valor_vendido'])}", subtitle_style))
        elements.append(Paragraph(f"Custo total: {formatarMoeda(relatorio_data['meta']['total_custo'])}", subtitle_style))
        elements.append(Paragraph(f"Lucro bruto total: {formatarMoeda(relatorio_data['meta']['lucro_bruto'])}", subtitle_style))
        
        # Lucro líquido com destaque
        lucro_liquido = relatorio_data['meta']['lucro_liquido']
        lucro_style = ParagraphStyle(
            'LucroStyle',
            parent=subtitle_style,
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=colors.darkgreen if lucro_liquido >= 0 else colors.red
        )
        elements.append(Paragraph(f"Lucro líquido total: {formatarMoeda(lucro_liquido)}", lucro_style))
        
        elements.append(Spacer(1, 15))
        
        # Verificar se é detalhado ou geral
        produto_id = request.args.get('produto_id')
        if produto_id:
            # MODO DETALHADO - Para um produto específico
            detalhes_data = relatorio_vendas_produtos_detalhes().get_json()
            if not detalhes_data.get('success'):
                return jsonify(detalhes_data), 500

            # Título do produto
            produto_title_style = ParagraphStyle(
                'ProdutoTitle',
                parent=styles['Heading2'],
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            elements.append(Paragraph(f"Detalhes do Produto: {detalhes_data['produto']['produto_nome']}", produto_title_style))
            
            # Tabela de informações do produto
            produto_info_data = [
                ['Código:', detalhes_data['produto']['produto_id']],
                ['Nome:', detalhes_data['produto']['produto_nome']],
                ['Unidade:', detalhes_data['produto']['unidade']],
                ['Quantidade Vendida:', f"{detalhes_data['produto']['quantidade_vendida']}"],
                ['Valor Total Vendido:', formatarMoeda(detalhes_data['produto']['valor_total_vendido'])],
                ['Custo Total:', formatarMoeda(detalhes_data['produto']['custo_total'])],
                ['Lucro Bruto:', formatarMoeda(detalhes_data['produto']['lucro_bruto'])],
                ['Estoque Atual:', f"{detalhes_data['produto']['estoque_atual_loja']}"]
            ]
            
            produto_table = Table(produto_info_data, colWidths=[60*mm, 100*mm])
            produto_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(produto_table)
            elements.append(Spacer(1, 15))
            
            # Histórico de vendas
            elements.append(Paragraph('Histórico de Vendas:', styles['Heading2']))
            
            if detalhes_data['historico']:
                # Cabeçalho da tabela
                historico_data = [['Data', 'Qtd.', 'Valor Unit.', 'Valor Total', 'Cliente']]
                
                # Dados das vendas
                for venda in detalhes_data['historico']:
                    data = datetime.fromisoformat(venda['data_emissao']).strftime('%d/%m/%Y')
                    cliente_nome = venda['cliente_nome'] or 'Consumidor'
                    if len(cliente_nome) > 30:
                        cliente_nome = cliente_nome[:27] + '...'
                    
                    historico_data.append([
                        data,
                        str(venda['quantidade']),
                        formatarMoeda(venda['valor_unitario']),
                        formatarMoeda(venda['valor_total']),
                        cliente_nome
                    ])
                
                # Criar tabela
                historico_table = Table(historico_data, colWidths=[25*mm, 20*mm, 30*mm, 30*mm, 85*mm])
                historico_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4682B4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (4, 1), (4, -1), 'LEFT'),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                
                elements.append(historico_table)
            else:
                elements.append(Paragraph('Nenhuma venda encontrada para este período.', normal_style))
                
        else:
            # MODO GERAL - Lista de produtos
            elements.append(Paragraph('Lista de Produtos:', styles['Heading2']))
            
            if relatorio_data['dados']:
                # Cabeçalho da tabela
                table_data = [['ID', 'Produto', 'Unid.', 'Qtd.', 'Vendas', 'Custo', 'Lucro', 'Estoque']]
                
                # Dados dos produtos
                for produto in relatorio_data['dados']:
                    # Truncar nome do produto se necessário
                    nome_produto = produto['produto_nome']
                    if len(nome_produto) > 40:
                        nome_produto = nome_produto[:37] + '...'
                    
                    table_data.append([
                        str(produto['produto_id']),
                        nome_produto,
                        produto['unidade'],
                        str(round(produto['quantidade_vendida'], 2)),
                        formatarMoeda(produto['valor_total_vendido']),
                        formatarMoeda(produto['custo_total']),
                        formatarMoeda(produto['lucro_bruto']),
                        str(round(produto['estoque_atual_loja'], 2))
                    ])
                
                # Criar tabela
                col_widths = [15*mm, 60*mm, 15*mm, 15*mm, 20*mm, 20*mm, 20*mm, 15*mm]
                produto_table = Table(table_data, colWidths=col_widths, repeatRows=1)
                
                # Estilo da tabela
                table_style = TableStyle([
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4682B4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                    ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ])
                
                # Adicionar cores para lucro positivo/negativo
                for i in range(1, len(table_data)):
                    lucro = produto['lucro_bruto'] if i == 1 else relatorio_data['dados'][i-1]['lucro_bruto']
                    if lucro < 0:
                        table_style.add('TEXTCOLOR', (6, i), (6, i), colors.red)
                    else:
                        table_style.add('TEXTCOLOR', (6, i), (6, i), colors.darkgreen)
                
                produto_table.setStyle(table_style)
                elements.append(produto_table)
            else:
                elements.append(Paragraph('Nenhum produto encontrado para este período.', normal_style))
        
        # Gerar PDF
        doc.build(elements)
        
        # Preparar resposta
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=relatorio_vendas_produtos.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def formatarMoeda(valor):
    """Função auxiliar para formatar valores monetários"""
    return f"R$ {float(valor):,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')

# ================= CONTAS A RECEBER =====================
@admin_bp.route('/contas-receber', methods=['GET'])
@login_required
@admin_required
def contas_receber():
    # Obter parâmetros de filtro
    cliente_nome = request.args.get('cliente_nome', '').strip()
    cliente_documento = request.args.get('cliente_documento', '').strip()
    data_emissao_inicio = request.args.get('data_emissao_inicio')
    data_emissao_fim = request.args.get('data_emissao_fim')
    data_vencimento_inicio = request.args.get('data_vencimento_inicio')
    data_vencimento_fim = request.args.get('data_vencimento_fim')
    status = request.args.get('status')

    # Query base
    query = ContaReceber.query.join(Cliente)
    
    # Filtros
    if cliente_nome:
        query = query.filter(Cliente.nome.ilike(f'%{cliente_nome}%'))
    
    if cliente_documento:
        query = query.filter(Cliente.documento.ilike(f'%{cliente_documento}%'))
    
    # Filtro por data de emissão
    if data_emissao_inicio:
        try:
            data_emissao_inicio = datetime.strptime(data_emissao_inicio, '%Y-%m-%d').date()
            query = query.filter(ContaReceber.data_emissao >= data_emissao_inicio)
        except ValueError:
            pass
    
    if data_emissao_fim:
        try:
            data_emissao_fim = datetime.strptime(data_emissao_fim, '%Y-%m-%d').date()
            query = query.filter(ContaReceber.data_emissao <= data_emissao_fim)
        except ValueError:
            pass
    
    # Filtro por data de vencimento
    if data_vencimento_inicio:
        try:
            data_vencimento_inicio = datetime.strptime(data_vencimento_inicio, '%Y-%m-%d').date()
            query = query.filter(ContaReceber.data_vencimento >= data_vencimento_inicio)
        except ValueError:
            pass
    
    if data_vencimento_fim:
        try:
            data_vencimento_fim = datetime.strptime(data_vencimento_fim, '%Y-%m-%d').date()
            query = query.filter(ContaReceber.data_vencimento <= data_vencimento_fim)
        except ValueError:
            pass

    # Filtro de status
    hoje = datetime.now().date()
    if status:
        if status == 'pendente':
            query = query.filter(
                ContaReceber.status != StatusPagamento.quitado,
                ContaReceber.data_vencimento >= hoje
            )
        elif status == 'atrasado':
            query = query.filter(
                ContaReceber.status != StatusPagamento.quitado,
                ContaReceber.data_vencimento < hoje
            )
        elif status == 'quitado':
            query = query.filter(ContaReceber.status == StatusPagamento.quitado)
        elif status == 'parcial':
            query = query.filter(
                ContaReceber.status != StatusPagamento.quitado,
                ContaReceber.valor_aberto > 0,
                ContaReceber.valor_aberto < ContaReceber.valor_original
            )
    
    # Executar query
    contas = query.order_by(ContaReceber.data_vencimento.asc()).all()

    # Serialização
    contas_json = []
    for conta in contas:
        contas_json.append({
            'id': conta.id,
            'cliente': {
                'nome': conta.cliente.nome,
                'documento': conta.cliente.documento
            },
            'descricao': conta.descricao,
            'valor_original': float(conta.valor_original),
            'valor_aberto': float(conta.valor_aberto),
            'data_emissao': conta.data_emissao.strftime('%Y-%m-%d'),
            'data_vencimento': conta.data_vencimento.strftime('%Y-%m-%d'),
            'status': conta.status.value
        })

    return jsonify({
        'success': True,
        'contas': contas_json
    })
    
@admin_bp.route('/contas-receber/<int:id>/detalhes', methods=['GET'])
@login_required
@admin_required
def conta_receber_detalhes(id):
    conta = ContaReceber.query.get_or_404(id)
    caixas = Caixa.query.order_by(Caixa.data_abertura.desc()).all()
    caixas_json = [{
        'id': c.id,
        'operador': c.operador.nome if c.operador else 'Sem operador',
        'data_abertura': c.data_abertura.strftime('%Y-%m-%d'),
        'status': c.status.value
    } for c in caixas]
    print(f'{caixas_json}')
    return jsonify({
        'id': conta.id,
        'cliente': conta.cliente.nome,
        'cliente_documento': conta.cliente.documento if conta.cliente and conta.cliente.documento else '',
        'descricao': conta.descricao,
        'valor_original': float(conta.valor_original),
        'valor_aberto': float(conta.valor_aberto),
        'data_emissao': conta.data_emissao.strftime('%d/%m/%Y'),
        'data_vencimento': conta.data_vencimento.strftime('%d/%m/%Y'),
        'status': conta.status.value,
        'nota_fiscal': {
            'id': conta.nota_fiscal_id,
            'valor_total': float(conta.nota_fiscal.valor_total) if conta.nota_fiscal else None
        } if conta.nota_fiscal else None,
        'pagamentos': [{
            'id': p.id,
            'valor_pago': float(p.valor_pago),
            'data_pagamento': p.data_pagamento.strftime('%d/%m/%Y'),
            'forma_pagamento': p.forma_pagamento.value,
            'observacoes': p.observacoes or ''
        } for p in conta.pagamentos],
        'caixas': caixas_json  
    })

@admin_bp.route('/contas-receber/<int:id>/pagar', methods=['POST'])
@login_required
@admin_required
def pagar_conta_receber(id):
    conta = ContaReceber.query.get_or_404(id)
    data = request.get_json()
    print(f'Dados recebidos para pagamento: {data}')  # Log completo dos dados

    try:
        # Validação do valor pago
        valor_pago = Decimal(str(data.get('valor_pago', 0)))
        if valor_pago <= 0:
            return jsonify({'error': 'Valor deve ser positivo'}), 400
        if valor_pago > conta.valor_aberto:
            return jsonify({'error': 'Valor excede o valor em aberto'}), 400

        # Forma de pagamento
        forma_pagamento_str = data.get('forma_pagamento')
        if not forma_pagamento_str:
            return jsonify({'error': 'Forma de pagamento não informada'}), 400
        try:
            forma_pagamento = FormaPagamento[forma_pagamento_str]
        except KeyError:
            return jsonify({'error': f'Forma de pagamento inválida: {forma_pagamento_str}'}), 400

        # Caixa
        caixa_id = data.get('caixa_id')
        if caixa_id is not None:
            try:
                caixa_id = int(caixa_id)
                if not Caixa.query.get(caixa_id):
                    return jsonify({'error': 'Caixa não encontrado'}), 400
            except ValueError:
                return jsonify({'error': 'ID do caixa inválido'}), 400
        else:
            caixa = Caixa.query.filter_by(
                operador_id=current_user.id,
                status=StatusCaixa.aberto
            ).order_by(Caixa.data_abertura.desc()).first()
            if caixa:
                caixa_id = caixa.id
            else:
                return jsonify({'error': 'Nenhum caixa aberto encontrado para o usuário'}), 400

        # Observações
        observacoes = data.get('observacoes', '')

        # SEMPRE usa a data e hora atuais, ignorando qualquer entrada do frontend
        data_pagamento = datetime.now()

        # REGISTRAR PAGAMENTO
        pagamento = conta.registrar_pagamento(
            valor_pago=valor_pago,
            forma_pagamento=forma_pagamento,
            caixa_id=caixa_id,
            observacoes=observacoes,
            data_pagamento=data_pagamento
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'valor_aberto': float(conta.valor_aberto),
            'status': conta.status.value,
            'data_pagamento': data_pagamento.strftime('%Y-%m-%d %H:%M:%S')  # Retorna data e hora completas
        })

    except Exception as e:
        import traceback
        db.session.rollback()
        print(f'Erro ao processar pagamento: {e}')
        print(traceback.format_exc())
        return jsonify({'error': f'Erro interno ao processar pagamento: {str(e)}'}), 500