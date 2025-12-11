import base64
from functools import wraps
from io import BytesIO
import textwrap
# Importações do Flask e sistema
from flask import current_app, request, jsonify, send_file
from datetime import datetime
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet
# Importações do ReportLab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import re
import threading
from flask import Blueprint, abort, json, make_response, render_template, request, jsonify, current_app as app
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from app import db
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.bot.bot_movimentacao import enviar_resumo_caixa_fechado, enviar_resumo_movimentacao_diaria
from flask import send_file
from app.utils.preparar_notas import preparar_dados_nota
from app.utils.converter_endereco import parse_endereco_string
from app.utils.format_data_moeda import format_currency, format_number
from app.utils.nfce import gerar_nfce_pdf_bobina_bytesio
from app.models.entities import (
     Caixa, Cliente, Configuracao, ContaReceber, Desconto, Entrega, Financeiro, LoteEstoque, NotaFiscal,
     NotaFiscalItem, PagamentoNotaFiscal, Produto, TipoDesconto, TipoEstoque, 
     TipoUsuario, produto_desconto_association, NotaFiscal, PagamentoContaReceber
)
from app.schemas import (
    ClienteCreate,
    ClienteBase,
    MovimentacaoEstoqueCreate,
)
from app.crud import (
    CategoriaFinanceira,
    FormaPagamento,
    StatusCaixa,
    StatusNota,
    StatusPagamento,
    TipoMovimentacao,
    buscar_pagamentos_notas_fiscais,
    estornar_venda,
    listar_despesas_dia_atual_formatado,
    listar_despesas_do_dia,
    obter_detalhes_vendas_dia,
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
import logging

operador_bp = Blueprint('operador', __name__, url_prefix='/operador')
logger = logging.getLogger(__name__)

def operador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
        if current_user.tipo != 'operador':  # Supondo que 'tipo' seja o campo que define o tipo de usuário
            return jsonify({'success': False, 'message': 'Acesso restrito a operadores'}), 403
        return f(*args, **kwargs)
    return decorated_function


@operador_bp.route('/dashboard')
@login_required
@operador_required
def dashboard():
    logger.info(f"Acessando dashboard do operador: {current_user.nome}")
    return render_template('dashboard_operador.html', nome_usuario=current_user.nome)

# ===== API CLIENTES =====
@operador_bp.route('/api/clientes', methods=['GET'])
@login_required
@operador_required
def api_get_clientes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # Query base
    query = Cliente.query.filter_by(ativo=True)
    
    # Aplica busca se existir
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Cliente.nome.ilike(search_term),
                Cliente.documento.ilike(search_term),
                Cliente.telefone.ilike(search_term),
                Cliente.email.ilike(search_term),
                Cliente.endereco.ilike(search_term)
            )
        )
    
    # Paginação
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'clientes': [{
            'id': cliente.id,
            'nome': cliente.nome,
            'documento': cliente.documento,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': cliente.endereco,
            'ativo': cliente.ativo
        } for cliente in pagination.items],
        'pagination': {
            'current_page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })

@operador_bp.route('/api/clientes', methods=['POST'])
@login_required
@operador_required
def api_create_cliente():
    data = request.get_json()
    try:
        cliente = ClienteCreate(**data)
        cliente.ativo = True
        db_cliente = create_cliente(db.session, cliente)
        logger.info(f"Cliente criado com sucesso: {db_cliente.nome} (ID: {db_cliente.id})")
        return jsonify({
            'id': db_cliente.id,
            'nome': db_cliente.nome,
            'documento': db_cliente.documento,
            'telefone': db_cliente.telefone,
            'email': db_cliente.email,
            'endereco': db_cliente.endereco
        }), 201
    except ValueError as e:
        logger.error(f"Erro ao criar cliente: {str(e)}")
        return jsonify({'error': str(e)}), 400

@operador_bp.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
@login_required
@operador_required
def api_update_cliente(cliente_id):
    data = request.get_json()
    try:
        cliente_data = ClienteBase(**data)
        db_cliente = update_cliente(db.session, cliente_id, cliente_data)
        logger.info(f"Cliente atualizado com sucesso: {db_cliente.nome} (ID: {db_cliente.id})")
        return jsonify({
            'id': db_cliente.id,
            'nome': db_cliente.nome,
            'documento': db_cliente.documento,
            'telefone': db_cliente.telefone,
            'email': db_cliente.email,
            'endereco': db_cliente.endereco
        })
    except ValueError as e:
        logger.error(f"Erro ao atualizar cliente ID {cliente_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400

@operador_bp.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required
@operador_required
def api_delete_cliente(cliente_id):
    try:
        success = delete_cliente(db.session, cliente_id)
        logger.info(f"Cliente ID {cliente_id} deletado com sucesso")
        return jsonify({'success': success}), 200
    except ValueError as e:
        logger.error(f"Erro ao deletar cliente ID {cliente_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400

# ===== API PRODUTOS =====
@operador_bp.route('/api/produtos', methods=['GET'])
@login_required
@operador_required
def api_get_produtos():
    try:
        produtos = get_produtos(db.session)
        
        produtos_formatados = []
        for produto in produtos:
            # Calcula o estoque total somando todos os locais de estoque
            estoque_total = produto.estoque_loja
            
            # Filtra apenas produtos com estoque total positivo
            if estoque_total > 0:
                produto_data = {
                    'id': produto.id,
                    'nome': produto.nome,
                    'codigo': produto.codigo,
                    'tipo': produto.tipo,
                    'marca': produto.marca,
                    'unidade': produto.unidade.value if produto.unidade else None,  # Converte o Enum para valor
                    'valor_unitario': float(produto.valor_unitario),
                    'estoque_loja': float(produto.estoque_loja),
                    'estoque_deposito': float(produto.estoque_deposito),
                    'estoque_fabrica': float(produto.estoque_fabrica),
                    'estoque_total': float(estoque_total),
                    'estoque_minimo': float(produto.estoque_minimo) if produto.estoque_minimo else None,
                    'estoque_maximo': float(produto.estoque_maximo) if produto.estoque_maximo else None,
                    'ativo': produto.ativo,
                    'descricao': f"{produto.nome} ({produto.marca})" if produto.marca else produto.nome,
                    'criado_em': produto.criado_em.isoformat() if produto.criado_em else None,
                    'atualizado_em': produto.atualizado_em.isoformat() if produto.atualizado_em else None
                }
                produtos_formatados.append(produto_data)
        
        return jsonify(produtos_formatados)
    
    except Exception as e:
        logger.error(f"Erro ao obter produtos: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao buscar produtos'}), 500

@operador_bp.route('/api/produtos/<int:produto_id>', methods=['GET'])
@login_required
@operador_required
def api_get_produto(produto_id):
    try:
        produto = get_produto(db.session, produto_id)
        if produto:
            estoque_total = produto.estoque_loja
            
            return jsonify({
                'id': produto.id,
                'nome': produto.nome,
                'codigo': produto.codigo,
                'tipo': produto.tipo,
                'marca': produto.marca,
                'unidade': produto.unidade.value if produto.unidade else None,
                'valor_unitario': float(produto.valor_unitario),
                'estoque_loja': float(produto.estoque_loja),
                'estoque_deposito': float(produto.estoque_deposito),
                'estoque_fabrica': float(produto.estoque_fabrica),
                'estoque_total': float(estoque_total),
                'estoque_minimo': float(produto.estoque_minimo) if produto.estoque_minimo else None,
                'estoque_maximo': float(produto.estoque_maximo) if produto.estoque_maximo else None,
                'ativo': produto.ativo,
                'criado_em': produto.criado_em.isoformat() if produto.criado_em else None,
                'atualizado_em': produto.atualizado_em.isoformat() if produto.atualizado_em else None,
                'sincronizado': produto.sincronizado
            })
        logger.warning(f"Produto não encontrado: {produto_id}")
        return jsonify({'error': 'Produto não encontrado'}), 404
    
    except Exception as e:
        logger.error(f"Erro ao obter produto ID {produto_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao buscar produto'}), 500

# ===== API VENDAS =====
@operador_bp.route('/api/vendas', methods=['POST'])
@login_required
@operador_required
def api_registrar_venda():
    # Verificação inicial do conteúdo da requisição
    config = Configuracao.get_config(db.session)
    permitir_venda_sem_estoque = config.permitir_venda_sem_estoque
    
    if not request.is_json:
        logger.error("Requisição sem cabeçalho Content-Type: application/json")
        return jsonify({
            'success': False,
            'message': 'Content-Type deve ser application/json'
        }), 400

    try:
        dados_venda = request.get_json()
        if dados_venda is None:
            logger.error("Nenhum dado JSON recebido ou JSON inválido")
            return jsonify({
                'success': False,
                'message': 'JSON inválido ou não enviado'
            }), 400

        # Campos obrigatórios
        required_fields = ['cliente_id', 'itens', 'pagamentos', 'valor_total']
        for field in required_fields:
            if field not in dados_venda:
                logger.error(f"Campo obrigatório faltando: {field}")
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório faltando: {field}'
                }), 400

        # Validação de tipos
        if not isinstance(dados_venda['itens'], list) or len(dados_venda['itens']) == 0:
            logger.error("Lista de itens inválida ou vazia")
            return jsonify({
                'success': False,
                'message': 'Lista de itens inválida ou vazia'
            }), 400

        if not isinstance(dados_venda['pagamentos'], list) or len(dados_venda['pagamentos']) == 0:
            logger.error("Lista de pagamentos inválida ou vazia")
            return jsonify({
                'success': False,
                'message': 'Lista de pagamentos inválida ou vazia'
            }), 400

        # Conversão e validação de valores
        try:
            cliente_id = int(dados_venda['cliente_id'])
            valor_total = Decimal(str(dados_venda['valor_total']))
            total_descontos = Decimal(str(dados_venda.get('total_descontos', 0)))
            
            # Calcula o valor total dos pagamentos que não são a prazo
            valor_a_vista = sum(
                Decimal(str(p.get('valor'))) 
                for p in dados_venda['pagamentos'] 
                if p.get('forma_pagamento') != 'a_prazo'
            )
            
            # O valor recebido é apenas o que não é a prazo
            valor_recebido = valor_a_vista
        except (ValueError, InvalidOperation) as e:
            logger.error(f"Erro na conversão de valores: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Valores numéricos inválidos'
            }), 400

        # Consultar cliente
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            logger.error(f"Cliente não encontrado: ID {cliente_id}")
            return jsonify({
                'success': False,
                'message': f'Cliente não encontrado: ID {cliente_id}'
            }), 404

        # Validar itens e estoque
        produtos_info = {}
        for item_data in dados_venda['itens']:
            try:
                produto_id = int(item_data.get('produto_id'))
                quantidade = Decimal(str(item_data.get('quantidade')))
                valor_unitario = Decimal(str(item_data.get('valor_unitario')))
                valor_total_item = Decimal(str(item_data.get('valor_total')))
                
                produto = Produto.query.get(produto_id)
                if not produto:
                    logger.error(f"Produto não encontrado: ID {produto_id}")
                    return jsonify({
                        'success': False,
                        'message': f'Produto não encontrado: ID {produto_id}'
                    }), 404

                # Verificar se há estoque suficiente
                if produto.estoque_loja < quantidade:
                    logger.error(f"Estoque insuficiente para produto: {produto.nome}")
                    if not permitir_venda_sem_estoque:
                        return jsonify({
                            'success': False,
                            'message': f'Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque_loja}'
                        }), 400
                    else:
                        logger.warning(f"Venda sem estoque permitida para produto: {produto.nome}")

                # Verificar se há lotes suficientes
                lotes_disponiveis = LoteEstoque.query.filter(
                    LoteEstoque.produto_id == produto_id,
                    LoteEstoque.quantidade_disponivel > 0
                ).order_by(LoteEstoque.data_entrada.asc()).all()

                quantidade_necessaria = quantidade
                for lote in lotes_disponiveis:
                    if quantidade_necessaria <= 0:
                        break
                    if lote.quantidade_disponivel >= quantidade_necessaria:
                        quantidade_necessaria = Decimal('0')
                    else:
                        quantidade_necessaria -= lote.quantidade_disponivel

                if quantidade_necessaria > 0:
                    logger.error(f"Lotes insuficientes para produto: {produto.nome}")
                    if not permitir_venda_sem_estoque:
                        return jsonify({
                            'success': False,
                            'message': f'Lotes insuficientes para {produto.nome}. Quantidade faltante: {quantidade_necessaria}'
                        }), 400
                    else:
                        logger.warning(f"Lotes insuficientes, mas venda permitida: {produto.nome}")

                produtos_info[produto_id] = {
                    'produto': produto,
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario,
                    'valor_total_item': valor_total_item
                }

            except (ValueError, InvalidOperation, TypeError) as e:
                logger.error(f"Erro ao processar item: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Dados do item inválidos'
                }), 400

        # Verificar soma dos pagamentos
        try:
            soma_pagamentos = sum(Decimal(str(p.get('valor'))) for p in dados_venda['pagamentos'])
            a_prazo_usado = any(p.get('forma_pagamento') == 'a_prazo' for p in dados_venda['pagamentos'])
            
            # Verificar se a soma dos pagamentos é igual ao valor total (com tolerância para arredondamento)
            diferenca = abs(soma_pagamentos - valor_total)
            if diferenca > Decimal('0.01'):  # Tolerância de 1 centavo
                logger.error(f"Soma dos pagamentos ({soma_pagamentos}) não confere com valor total ({valor_total})")
                return jsonify({
                    'success': False,
                    'message': f'Soma dos pagamentos ({soma_pagamentos}) não confere com valor total ({valor_total})'
                }), 400
                
        except (ValueError, InvalidOperation, TypeError) as e:
            logger.error(f"Erro ao verificar pagamentos: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Dados de pagamento inválidos'
            }), 400

        # Verificar caixa aberto
        caixa_aberto = get_caixa_aberto(db.session, operador_id=current_user.id)
        
        if not caixa_aberto:
            logger.error("Nenhum caixa aberto encontrado")
            return jsonify({
                'success': False,
                'message': 'Nenhum caixa aberto encontrado'
            }), 400

        # Criar registro de Nota Fiscal
        nota = NotaFiscal(
            cliente_id=cliente.id,
            operador_id=current_user.id,
            caixa_id=caixa_aberto.id,
            data_emissao=datetime.now(),
            valor_total=valor_total,
            valor_desconto=total_descontos,
            tipo_desconto=None,
            status=StatusNota.emitida,
            forma_pagamento=FormaPagamento.dinheiro,  # Será atualizado abaixo
            valor_recebido=valor_recebido,
            troco=max(valor_recebido - valor_total, Decimal(0)) if not a_prazo_usado else Decimal(0),
            a_prazo=a_prazo_usado,
            observacao=dados_venda.get('observacao', '')
        )

        # Criar Entrega, se presente - COM TRATAMENTO SEGURO
        endereco_entrega = dados_venda.get('endereco_entrega')
        if endereco_entrega and isinstance(endereco_entrega, dict):
            entrega = Entrega(
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

        # Criar itens da nota fiscal e processar lotes
        for item_data in dados_venda['itens']:
            produto_id = item_data.get('produto_id')
            produto_info = produtos_info[produto_id]
            produto = produto_info['produto']
            quantidade = produto_info['quantidade']
            valor_unitario = produto_info['valor_unitario']
            valor_total_item = produto_info['valor_total_item']
            desconto_aplicado = Decimal(str(item_data.get('valor_desconto', 0)))
            
            # Tratamento seguro para desconto_info
            desconto_info = item_data.get('desconto_info', {}) or {}
            tipo_desconto = desconto_info.get('tipo') if isinstance(desconto_info, dict) else None

            # BUSCAR LOTES DO PRODUTO ORDENADOS POR DATA DE ENTRADA (MAIS ANTIGO PRIMEIRO)
            lotes = LoteEstoque.query.filter(
                LoteEstoque.produto_id == produto_id,
                LoteEstoque.quantidade_disponivel > 0
            ).order_by(LoteEstoque.data_entrada.asc()).all()

            quantidade_restante = quantidade
            valor_unitario_compra_final = Decimal('0')
            total_custo = Decimal('0')
            quantidade_total_usada = Decimal('0')

            # PROCESSAR LOTES PARA DAR SAÍDA (PEPS - Primeiro a Entrar, Primeiro a Sair)
            for lote in lotes:
                if quantidade_restante <= 0:
                    break
                    
                if lote.quantidade_disponivel > 0:
                    quantidade_a_usar = min(quantidade_restante, lote.quantidade_disponivel)
                    
                    # Atualizar lote
                    lote.quantidade_disponivel -= quantidade_a_usar
                    quantidade_restante -= quantidade_a_usar
                    quantidade_total_usada += quantidade_a_usar
                    
                    # Acumular custo para cálculo da média ponderada
                    total_custo += quantidade_a_usar * lote.valor_unitario_compra
                    
                    # Se este foi o último lote usado, definir como valor_unitario_compra_final
                    if quantidade_restante == 0:
                        valor_unitario_compra_final = lote.valor_unitario_compra

            # Calcular valor unitário de compra médio ponderado se usou múltiplos lotes
            if quantidade_total_usada > 0:
                valor_unitario_compra_final = total_custo / quantidade_total_usada

            # VERIFICAR SE O ESTOQUE SERÁ ZERADO E ATUALIZAR COM O PRÓXIMO LOTE VÁLIDO
            estoque_atual = produto.estoque_loja
            estoque_futuro = estoque_atual - quantidade
            estoque_zerado = estoque_futuro == 0

            if estoque_zerado:
                # Buscar o próximo lote mais antigo com quantidade válida (se existir)
                proximo_lote_valido = LoteEstoque.query.filter(
                    LoteEstoque.produto_id == produto_id,
                    LoteEstoque.quantidade_disponivel > 0
                ).order_by(LoteEstoque.data_entrada.asc()).first()
                
                if proximo_lote_valido:
                    # Se há próximo lote válido, usar seu valor_unitario_compra
                    produto.valor_unitario_compra = proximo_lote_valido.valor_unitario_compra
                    logger.info(f"Estoque zerado para produto {produto.nome}. Atualizado valor_unitario_compra para: {proximo_lote_valido.valor_unitario_compra}")
                else:
                    # Se não há mais lotes, manter o último valor usado ou definir como 0
                    if valor_unitario_compra_final > 0:
                        produto.valor_unitario_compra = valor_unitario_compra_final
                    else:
                        # Se não temos valor final e não há lotes, manter o atual
                        produto.valor_unitario_compra = produto.valor_unitario_compra if produto.valor_unitario_compra else Decimal('0')
                    logger.info(f"Estoque zerado para produto {produto.nome}. Sem lotes disponíveis. Valor mantido: {produto.valor_unitario_compra}")
            elif valor_unitario_compra_final > 0:
                # Se o estoque não foi zerado mas temos um valor final válido, atualizar
                produto.valor_unitario_compra = valor_unitario_compra_final
                logger.info(f"Produto {produto.nome}. valor_unitario_compra atualizado para: {valor_unitario_compra_final}")

            item_nf = NotaFiscalItem(
                nota_id=nota.id,
                produto_id=produto_id,
                estoque_origem=TipoEstoque.loja,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total_item,
                desconto_aplicado=desconto_aplicado,
                tipo_desconto=TipoDesconto(tipo_desconto) if tipo_desconto else None,
                sincronizado=False
            )
            db.session.add(item_nf)
            
            # Atualizar estoque do produto
            produto.estoque_loja = estoque_futuro

        # Criar pagamentos e armazenar seus IDs
        pagamentos_ids = []
        valor_a_prazo = Decimal(0)
        
        for pagamento_data in dados_venda['pagamentos']:
            forma = pagamento_data.get('forma_pagamento')
            valor = Decimal(str(pagamento_data.get('valor')))
            
            pagamento_nf = PagamentoNotaFiscal(
                nota_fiscal_id=nota.id,
                forma_pagamento=FormaPagamento(forma),
                valor=valor,
                data=datetime.now(),
                sincronizado=False
            )
            db.session.add(pagamento_nf)
            db.session.flush()  # Garante que teremos o ID do pagamento
            
            pagamentos_ids.append(pagamento_nf.id)
            
            # Registrar no financeiro APENAS se não for a prazo
            if forma != 'a_prazo':
                financeiro = Financeiro(
                    tipo=TipoMovimentacao.entrada,
                    categoria=CategoriaFinanceira.venda,
                    valor=valor,
                    descricao=f"Pagamento venda NF #{nota.id}",
                    cliente_id=cliente.id,
                    caixa_id=caixa_aberto.id,
                    nota_fiscal_id=nota.id,
                    pagamento_id=pagamento_nf.id,
                    sincronizado=False
                )
                db.session.add(financeiro)
            else:
                valor_a_prazo += valor

        # Se houver pagamento a prazo, criar conta a receber
        if a_prazo_usado and valor_a_prazo > 0:
            conta_receber = ContaReceber(
                cliente_id=cliente.id,
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo NF #{nota.id}",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=datetime.now() + timedelta(days=30),
                status=StatusPagamento.pendente,
                sincronizado=False
            )
            db.session.add(conta_receber)

        # Atualizar a forma de pagamento principal da nota fiscal
        if len(dados_venda['pagamentos']) == 1:
            # Se houver apenas um pagamento, usa essa forma
            nota.forma_pagamento = FormaPagamento(dados_venda['pagamentos'][0]['forma_pagamento'])
        else:
            # Se houver múltiplos pagamentos, define como "misto"
            nota.forma_pagamento = FormaPagamento.dinheiro  # Ou criar um enum para "misto"

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Venda registrada com sucesso',
            'nota_fiscal_id': nota.id,
            'pagamentos_ids': pagamentos_ids,
            'valor_total': float(valor_total),
            'valor_recebido': float(valor_recebido),
            'troco': float(nota.troco) if nota.troco else 0,
            'valor_a_prazo': float(valor_a_prazo) if a_prazo_usado else 0
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Erro no banco ao registrar venda: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Erro ao registrar venda no banco',
            'error': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro inesperado ao registrar venda: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Erro inesperado ao registrar venda',
            'error': str(e)
        }), 500
        
@operador_bp.route('/pdf/nota/<id_list>', methods=['GET'])
@login_required
@operador_required
def visualizar_pdf_venda(id_list):
    try:
        # Converter string de IDs para lista de inteiros
        ids = [int(id.strip()) for id in id_list.split(',')] if ',' in id_list else [int(id_list)]
        
        # Buscar os dados das notas fiscais
        resultado_busca = buscar_pagamentos_notas_fiscais(db.session, ids)
        if not resultado_busca or not resultado_busca['data']:
            abort(404, description="Nenhuma nota encontrada com os IDs fornecidos")
        
        # Pegar os dados da primeira nota (mesmo para múltiplas notas)
        dados_nota = resultado_busca['data'][0]
        # Gerar PDF em memória com os dados completos
        pdf_buffer = gerar_nfce_pdf_bobina_bytesio(dados_nota=dados_nota)
        
        # Criar resposta para abrir em nova guia
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=nota_{dados_nota["nota_fiscal_id"]}.pdf'
        
        return response
        
    except ValueError:
        abort(400, description="Formato inválido. Use um número ou números separados por vírgula (ex: 44 ou 44,45)")
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {str(e)}")
        abort(500, description="Ocorreu um erro ao gerar o PDF")

@operador_bp.route('/pdf/nota-venda/<int:venda_id>', methods=['GET'])
@login_required
@operador_required
def download_nota_venda(venda_id):
    try:
        # Buscar os detalhes da venda usando a mesma lógica da rota de detalhes
        nota_fiscal = NotaFiscal.query.get_or_404(venda_id)
        
        # Buscar pagamentos associados
        pagamentos = PagamentoNotaFiscal.query.filter_by(
            nota_fiscal_id=venda_id
        ).all()
        
        # Remover duplicatas
        pagamentos_unicos = []
        ids_vistos = set()
        
        for pagamento in pagamentos:
            if pagamento.id not in ids_vistos:
                ids_vistos.add(pagamento.id)
                pagamentos_unicos.append(pagamento)
        
        # Preparar dados no formato esperado pelo gerador de PDF
        dados_nota = {
            "nota_fiscal_id": nota_fiscal.id,
            "data_emissao": nota_fiscal.data_emissao.isoformat(),
            "valor_total_nota": float(nota_fiscal.valor_total),
            "valor_total_sem_desconto": float(nota_fiscal.valor_total + nota_fiscal.valor_desconto),
            "operador": {
                "nome": nota_fiscal.operador.nome
            },
            "cliente": {
                "nome": nota_fiscal.cliente.nome if nota_fiscal.cliente else "Consumidor Final",
                "documento": nota_fiscal.cliente.documento if nota_fiscal.cliente else None
            },
            "produtos": [
                {
                    "id": item.id,
                    "nome": item.produto.nome,
                    "quantidade": float(item.quantidade),
                    "valor_unitario": float(item.valor_unitario),
                    "valor_total_com_desconto": float(item.valor_total),
                    "desconto_aplicado": float(item.desconto_aplicado) if item.desconto_aplicado else 0.0
                }
                for item in nota_fiscal.itens
            ],
            "formas_pagamento": [
                {
                    "forma_pagamento": pagamento.forma_pagamento.value,
                    "valor": float(pagamento.valor)
                }
                for pagamento in pagamentos_unicos
            ],
            "endereco_entrega": {
                "logradouro": nota_fiscal.entrega.logradouro if nota_fiscal.entrega else None,
                "numero": nota_fiscal.entrega.numero if nota_fiscal.entrega else None,
                "complemento": nota_fiscal.entrega.complemento if nota_fiscal.entrega else None,
                "bairro": nota_fiscal.entrega.bairro if nota_fiscal.entrega else None,
                "cidade": nota_fiscal.entrega.cidade if nota_fiscal.entrega else None,
                "estado": nota_fiscal.entrega.estado if nota_fiscal.entrega else None,
                "cep": nota_fiscal.entrega.cep if nota_fiscal.entrega else None,
                "instrucoes": nota_fiscal.entrega.instrucoes if nota_fiscal.entrega else None
            } if nota_fiscal.entrega else None,
            "metadados": {
                "possui_entrega": nota_fiscal.entrega is not None
            }
        }
        
        # Gerar PDF em memória
        pdf_buffer = gerar_nfce_pdf_bobina_bytesio(dados_nota=dados_nota)
        
        # Criar resposta para abrir em nova guia (inline)
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=nota_venda_{venda_id}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF da venda {venda_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar PDF: {str(e)}'
        }), 500

@operador_bp.route('/api/vendas/hoje', methods=['GET'])
@login_required
@operador_required
def obter_vendas_hoje():
    try:
        # Obtém parâmetros de filtro com validação
        data_str = request.args.get('data')
        operador_id = request.args.get('operador_id', type=int)
        
        # Verificação robusta do caixa
        caixa = get_caixa_aberto(db.session, operador_id=current_user.id)
        if not caixa:
            logger.error("Nenhum caixa aberto para o operador atual")
            return jsonify({
                'success': False,
                'message': 'Nenhuma venda a exibir! Caixa Fechado!'
            }), 400

        # Tratamento de data com fuso horário
        tz = ZoneInfo('America/Sao_Paulo')
        data_hoje = datetime.now(tz).date()
        data_filtro = data_hoje
        
        if data_str:
            try:
                data_filtro = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Formato de data inválido: {data_str}")
                return jsonify({
                    'success': False,
                    'message': 'Formato de data inválido. Use YYYY-MM-DD'
                }), 400

        # Construção da query com prevenção de duplicatas
        inicio_dia = datetime.combine(data_filtro, time.min).replace(tzinfo=tz)
        fim_dia = datetime.combine(data_filtro, time.max).replace(tzinfo=tz)

        # Query principal com distinct para evitar duplicatas no JOIN
        vendas = db.session.query(NotaFiscal).distinct(
            NotaFiscal.id
        ).options(
            db.joinedload(NotaFiscal.cliente),
            db.joinedload(NotaFiscal.operador),
            db.joinedload(NotaFiscal.caixa),
            db.joinedload(NotaFiscal.itens).joinedload(NotaFiscalItem.produto),
            db.joinedload(NotaFiscal.pagamentos)  # Carrega os pagamentos
        ).filter(
            NotaFiscal.caixa_id == caixa.id,
            NotaFiscal.status == StatusNota.emitida,
            NotaFiscal.data_emissao >= inicio_dia,
            NotaFiscal.data_emissao <= fim_dia
        )

        # Filtro adicional por operador
        if operador_id and operador_id != current_user.id:
            # Verifica se o usuário tem permissão para consultar outros operadores
            if not current_user.tipo == TipoUsuario.admin:
                logger.error(f"Operador {current_user.nome} tentou acessar vendas de outro operador sem permissão")
                return jsonify({
                    'success': False,
                    'message': 'Apenas administradores podem filtrar por outros operadores'
                }), 403
            vendas = vendas.filter(NotaFiscal.operador_id == operador_id)
        else:
            vendas = vendas.filter(NotaFiscal.operador_id == current_user.id)

        # Execução da query
        vendas_lista = vendas.order_by(NotaFiscal.data_emissao.desc()).all()

        # Processamento dos resultados com verificação de duplicatas
        ids_vistas = set()
        vendas_unicas = []
        
        for venda in vendas_lista:
            if venda.id in ids_vistas:
                continue
            ids_vistas.add(venda.id)
            vendas_unicas.append(venda)

        # Formatação final
        resultado = []
        total_geral = Decimal('0.00')
        
        for venda in vendas_unicas:
            total_venda = Decimal(str(venda.valor_total))
            total_geral += total_venda
            
            # Formatar formas de pagamento
            formas_pagamento = []
            if venda.pagamentos:
                for pagamento in venda.pagamentos:
                    formas_pagamento.append({
                        'forma_pagamento': pagamento.forma_pagamento.value,
                        'valor': float(pagamento.valor)
                    })
            
            resultado.append({
                'id': venda.id,
                'data_emissao': venda.data_emissao.strftime("%d/%m/%Y, %H:%M"),
                'cliente': {
                    'id': venda.cliente.id if venda.cliente else None,
                    'nome': venda.cliente.nome if venda.cliente else 'Consumidor Final'
                },
                'operador': {
                    'id': venda.operador.id,
                    'nome': venda.operador.nome
                },
                'valor_total': float(total_venda),
                'valor_desconto': float(venda.valor_desconto),
                'itens': [
                    {
                        'produto_id': item.produto.id,
                        'nome': item.produto.nome,
                        'quantidade': float(item.quantidade),
                        'valor_unitario': float(item.valor_unitario),
                        'total': float(item.valor_total)
                    }
                    for item in venda.itens
                ],
                'pagamentos': formas_pagamento,  # Agora inclui todas as formas de pagamento
                'forma_pagamento': venda.forma_pagamento.value if venda.forma_pagamento else None  # Mantém compatibilidade
            })
        
        return jsonify({
            'success': True,
            'data': resultado,
            'total_vendas': len(vendas_unicas),
            'total_valor': float(total_geral),
            'periodo': {
                'inicio': inicio_dia.isoformat(),
                'fim': fim_dia.isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Erro em obter_vendas_hoje: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Erro interno ao processar vendas'
        }), 500
    
@operador_bp.route('/api/despesas/hoje', methods=['GET'])
@login_required
@operador_required
def api_despesas_hoje():
    """API que retorna as despesas do dia atual."""
    try:
        despesas = listar_despesas_dia_atual_formatado(db.session)

        return jsonify({"sucesso": True, "despesas": despesas}), 200
    except Exception as e:
        print(e)
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@operador_bp.route('/api/vendas/resumo-diario', methods=['GET'])
@login_required
@operador_required
def resumo_vendas_diarias():
    try:
        data_str = request.args.get('data')
        data = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        
        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = datetime.combine(data, datetime.max.time())
        
        # Total de vendas (apenas em caixas abertos)
        total_vendas = db.session.query(func.count( NotaFiscal.id)).join(
             Caixa,
             NotaFiscal.caixa_id ==  Caixa.id
        ).filter(
             NotaFiscal.data_emissao >= inicio_dia,
             NotaFiscal.data_emissao <= fim_dia,
             NotaFiscal.status == StatusNota.emitida,
             Caixa.status == StatusCaixa.aberto  # Filtro por caixas abertos
        ).scalar()
        
        # Valor total vendido (apenas em caixas abertos)
        valor_total = db.session.query(func.coalesce(func.sum( NotaFiscal.valor_total), 0)).join(
             Caixa,
             NotaFiscal.caixa_id ==  Caixa.id
        ).filter(
             NotaFiscal.data_emissao >= inicio_dia,
             NotaFiscal.data_emissao <= fim_dia,
             NotaFiscal.status == StatusNota.emitida,
             Caixa.status == StatusCaixa.aberto  # Filtro por caixas abertos
        ).scalar()
        
        # Formas de pagamento (apenas em caixas abertos)
        formas_pagamento = db.session.query(
             NotaFiscal.forma_pagamento,
            func.count( NotaFiscal.id).label('quantidade'),
            func.sum( NotaFiscal.valor_total).label('valor_total')
        ).join(
             Caixa,
             NotaFiscal.caixa_id ==  Caixa.id
        ).filter(
             NotaFiscal.data_emissao >= inicio_dia,
             NotaFiscal.data_emissao <= fim_dia,
             NotaFiscal.status == StatusNota.emitida,
             Caixa.status == StatusCaixa.aberto  # Filtro por caixas abertos
        ).group_by( NotaFiscal.forma_pagamento).all()
        
        return jsonify({
            'success': True,
            'data': {
                'data': data.isoformat(),
                'total_vendas': total_vendas,
                'valor_total': float(valor_total),
                'formas_pagamento': [
                    {
                        'forma': fp[0].value if fp[0] else None,
                        'quantidade': fp[1],
                        'valor_total': float(fp[2])
                    }
                    for fp in formas_pagamento
                ]
            }
        })
    
    except Exception as e:
        logger.error(f"Erro em resumo_vendas_diarias: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Erro ao obter resumo diário: {str(e)}'
        }), 500


@operador_bp.route('/api/vendas/<int:venda_id>/detalhes', methods=['GET'])
@login_required
@operador_required
def obter_detalhes_venda(venda_id):
    try:
        # Busca a nota fiscal principal
        nota_fiscal =  NotaFiscal.query.get_or_404(venda_id)
        
        # Busca os pagamentos associados e remove duplicatas
        pagamentos =  PagamentoNotaFiscal.query.filter_by(
            nota_fiscal_id=venda_id
        ).all()
        
        # Filtra pagamentos duplicados
        pagamentos_unicos = []
        ids_vistos = set()
        
        for pagamento in pagamentos:
            if pagamento.id not in ids_vistos:
                ids_vistos.add(pagamento.id)
                pagamentos_unicos.append(pagamento)
        
        # Formata a resposta
        detalhes = {
            'id': nota_fiscal.id,
            'data_emissao': nota_fiscal.data_emissao.isoformat(),
            'cliente': {
                'id': nota_fiscal.cliente.id if nota_fiscal.cliente else None,
                'nome': nota_fiscal.cliente.nome if nota_fiscal.cliente else 'Consumidor Final',
                'documento': nota_fiscal.cliente.documento if nota_fiscal.cliente else None,
                'telefone': nota_fiscal.cliente.telefone if nota_fiscal.cliente else None
            },
            'operador': {
                'id': nota_fiscal.operador.id,
                'nome': nota_fiscal.operador.nome
            },
            'valor_total': float(nota_fiscal.valor_total),
            'valor_desconto': float(nota_fiscal.valor_desconto),
            'forma_pagamento': nota_fiscal.forma_pagamento.value if nota_fiscal.forma_pagamento else None,
            'a_prazo': nota_fiscal.a_prazo,
            'observacao': nota_fiscal.observacao,
            'itens': [
                {
                    'produto_id': item.produto.id,
                    'produto_nome': item.produto.nome,
                    'quantidade': float(item.quantidade),
                    'valor_unitario': float(item.valor_unitario),
                    'valor_total': float(item.valor_total),
                    'desconto_aplicado': float(item.desconto_aplicado) if item.desconto_aplicado else None
                }
                for item in nota_fiscal.itens
            ],
            'pagamentos': [
                {
                    'id': pagamento.id,
                    'forma_pagamento': pagamento.forma_pagamento.value,
                    'valor': float(pagamento.valor),
                    'data': pagamento.data.isoformat()
                }
                for pagamento in pagamentos_unicos  # Usa a lista filtrada aqui
            ],
            'entrega': {
                'endereco': nota_fiscal.entrega.logradouro if nota_fiscal.entrega else None,
                'numero': nota_fiscal.entrega.numero if nota_fiscal.entrega else None,
                'complemento': nota_fiscal.entrega.complemento if nota_fiscal.entrega else None,
                'bairro': nota_fiscal.entrega.bairro if nota_fiscal.entrega else None,
                'cidade': nota_fiscal.entrega.cidade if nota_fiscal.entrega else None,
                'estado': nota_fiscal.entrega.estado if nota_fiscal.entrega else None,
                'cep': nota_fiscal.entrega.cep if nota_fiscal.entrega else None,
                'instrucoes': nota_fiscal.entrega.instrucoes if nota_fiscal.entrega else None
            } if nota_fiscal.entrega else None
        }
        
        return jsonify({
            'success': True,
            'data': detalhes
        })
    
    except Exception as e:
        logger.error(f"Erro em obter_detalhes_venda: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Erro ao obter detalhes da venda: {str(e)}'
        }), 500
        
@operador_bp.route('/api/vendas/<int:sale_id>/estornar', methods=['POST'])
@login_required
@operador_required
def rota_estornar_venda(sale_id):
    """
    Rota para estornar uma venda
    """
    try:
        dados = request.get_json()
        
        if not dados:
            logger.error("Dados para estorno não fornecidos")
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
            
        motivo_estorno = dados.get('motivo_estorno')
        if not motivo_estorno:
            logger.error("Motivo do estorno não fornecido")
            return jsonify({'success': False, 'message': 'Motivo do estorno é obrigatório'}), 400
            
        usuario_id = current_user.id
        
        resultado = estornar_venda(db, sale_id, motivo_estorno, usuario_id)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao estornar venda {sale_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno ao processar estorno'
        }), 500
        
@operador_bp.route('/api/vendas/relatorio-diario-pdf', methods=['GET'])
@login_required
@operador_required
def gerar_pdf_vendas_dia():
    from reportlab.lib.pagesizes import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from io import BytesIO
    from flask import send_file, request, jsonify, make_response, current_app
    from datetime import datetime
    from sqlalchemy import func, and_
    import os
    from PIL import Image as PILImage
    import math

    # Configuração IDÊNTICA para bobina 80mm
    bobina_width = 226  # Exatamente igual
    bobina_height = 3000  # Exatamente igual
    
    # Obter caixa aberto do operador atual
    caixa = get_caixa_aberto(db.session, operador_id=current_user.id)
    if not caixa:
        logger.error("Nenhum caixa aberto encontrado para o operador atual")
        return jsonify({'success': False, 'message': 'Nenhum caixa aberto encontrado para o operador'}), 400
    
    caixa_id = caixa.id

    # Tratar parâmetros de data
    data_str = request.args.get('data')
    data = None
    if data_str:
        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Formato de data inválido: {data_str}")
            return jsonify({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    data_relatorio = data if data else datetime.now().date()

    # Obter dados das vendas
    resultado = obter_detalhes_vendas_dia(data, caixa_id, current_user.id)
    if not resultado['success']:
        logger.error("Erro ao obter detalhes das vendas do dia")
        dados = {
            'vendas': [],
            'total_descontos': 0,
            'total_saidas': 0,
            'por_forma_pagamento': {}
        }
    else:
        dados = resultado['data']

    # BUSCAR CONTAS A RECEBER PAGAS NO DIA (igual ao método da outra rota)
    total_contas_receber_pagas = 0
    try:
        # Calcular início e fim do dia
        inicio_dia = datetime.combine(data_relatorio, datetime.min.time())
        fim_dia = datetime.combine(data_relatorio, datetime.max.time())
        
        # Buscar pagamentos de contas a receber (igual)
        total_contas_receber_pagas = db.session.query(
            func.sum(PagamentoContaReceber.valor_pago)
        ).filter(
            PagamentoContaReceber.caixa_id == caixa_id,
            PagamentoContaReceber.data_pagamento >= inicio_dia,
            PagamentoContaReceber.data_pagamento <= fim_dia
        ).scalar() or 0.0
        
        total_contas_receber_pagas = float(total_contas_receber_pagas)
            
    except Exception as e:
        logger.error(f"Erro ao buscar contas a receber pagas: {str(e)}", exc_info=True)
        total_contas_receber_pagas = 0

    buffer = BytesIO()

    # Criar documento EXATAMENTE IGUAL
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(bobina_width, bobina_height),
        leftMargin=5,
        rightMargin=5,
        topMargin=-6,  # Exatamente igual
        bottomMargin=5
    )
    elements = []

    # --- Estilos EXATAMENTE IGUAIS ---
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

    # --- Funções auxiliares EXATAMENTE IGUAIS ---
    def moeda_br(valor):
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def linha_separadora():
        return Paragraph("=" * 34, linha_style)

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
            ('FONTSIZE', (0,0), (-1,-1), 12),  # Exatamente 12 como na outra
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        return tabela

    # --- Logo EXATAMENTE IGUAL ---
    logo_path = os.path.join(current_app.root_path, 'static', 'assets', 'logo.jpeg')
    if os.path.exists(logo_path):
        try:
            with PILImage.open(logo_path) as img:
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
            logo_width = 250  # Exatamente igual
            logo_height = logo_width / aspect_ratio
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(0, 6))  # Exatamente 6
        except Exception as e:
            logger.error(f"Erro ao carregar a logo: {e}")

    # --- Cabeçalho EXATAMENTE IGUAL ---
    elements.append(Paragraph("RELATÓRIO DIÁRIO DE VENDAS", header_style))
    elements.append(linha_separadora())
    elements.append(Spacer(1, 6))
    
    # Informações (layout igual)
    elements.append(Paragraph(f"Data: {data_relatorio.strftime('%d/%m/%Y')}", normal_style))
    elements.append(Paragraph(f"Operador: {current_user.nome}", normal_style))
    elements.append(Paragraph(f"Caixa: #{caixa_id}", normal_style))
    elements.append(Spacer(1, 6))

    # --- Resumo Financeiro (layout IDÊNTICO) ---
    elements.append(linha_separadora())
    elements.append(Paragraph("RESUMO FINANCEIRO", subtitle_style))
    elements.append(Spacer(1, 4))
    elements.append(linha_separadora())
    
    # Calcular valores como na outra rota
    total_vendas_positivas = sum(v['valor_total'] for v in dados['vendas'] if 'valor_total' in v and v['valor_total'] > 0) if 'vendas' in dados else 0
    total_estornos = sum(abs(v['valor_total']) for v in dados['vendas'] if 'valor_total' in v and v['valor_total'] < 0) if 'vendas' in dados else 0
    total_descontos = dados.get('total_descontos', 0)
    total_saidas = dados.get('total_saidas', 0)
    
    # Calcular formas de pagamento (igual ao método da outra rota)
    formas_pagamento = dados.get('por_forma_pagamento', {})
    
    # Calcular valor físico/digital como na outra rota
    valor_dinheiro = formas_pagamento.get('dinheiro', 0.0)
    valor_fisico = valor_dinheiro
    
    # EXATAMENTE IGUAL ao cálculo da outra rota
    if caixa.valor_fechamento and caixa.valor_abertura:
        valor_abertura = float(caixa.valor_abertura)
        valor_fechamento = float(caixa.valor_fechamento)
        valor_fisico = max((valor_dinheiro + valor_abertura) - valor_fechamento - total_saidas, 0.0)

        # Pega parte inteira e parte decimal (IGUAL)
        parte_inteira = math.floor(valor_fisico)
        parte_decimal = valor_fisico - parte_inteira

        # Código comentado mantido igual
        # if parte_decimal == 0.5:
        #     valor_fisico = valor_fisico
        # elif parte_decimal > 0.5:
        #     valor_fisico = math.ceil(valor_fisico)
        # else:
        #     valor_fisico = math.floor(valor_fisico)
    
    formas_pagamento['dinheiro'] = valor_fisico
    
    # Calcular valor digital IGUAL
    valor_digital = sum([
        formas_pagamento.get('pix_loja', 0.0),
        formas_pagamento.get('pix_fabiano', 0.0),
        formas_pagamento.get('pix_edfrance', 0.0),
        formas_pagamento.get('pix_maquineta', 0.0),
        formas_pagamento.get('cartao_debito', 0.0),
        formas_pagamento.get('cartao_credito', 0.0)
    ])

    a_prazo = formas_pagamento.get('a_prazo', 0.0)
    total_liquido = total_vendas_positivas - total_saidas
    
    # Linhas do resumo (ORDEM E FORMATO IDÊNTICOS)
    elements.append(linha_dupla("Total Entradas:", moeda_br(total_vendas_positivas)))
    elements.append(linha_dupla("Total Saídas:", moeda_br(total_saidas)))
    elements.append(linha_dupla("Saldo:", moeda_br(total_liquido)))
    elements.append(Spacer(1, 6))  # Espaço igual
    
    # Valores físicos/digitais (MESMA SEÇÃO)
    elements.append(linha_dupla("Valor Físico:", moeda_br(valor_fisico)))
    elements.append(linha_dupla("Valor Digital:", moeda_br(valor_digital)))
    elements.append(linha_dupla("A Prazo:", moeda_br(a_prazo)))
    elements.append(linha_dupla("A Prazo Recebidos:", moeda_br(total_contas_receber_pagas)))
    
    elements.append(Spacer(1, 4))
    elements.append(linha_separadora())
    elements.append(Spacer(1, 1))
    elements.append(Paragraph("Valores do Caixa", subtitle_style))  # MESMO SUBTÍTULO
    elements.append(Spacer(1, 6))
    elements.append(linha_separadora())
    
    # Valores de caixa (IGUAL)
    valor_abertura = float(caixa.valor_abertura) if caixa.valor_abertura else 0.0
    valor_fechamento = float(caixa.valor_fechamento) if caixa.valor_fechamento else 0.0
    
    elements.append(linha_dupla("Abertura:", moeda_br(valor_abertura)))
    elements.append(linha_dupla("Fechamento:", moeda_br(valor_fechamento)))
    
    # --- Formas de Pagamento (layout IDÊNTICO) ---
    elements.append(Spacer(1, 4))
    elements.append(linha_separadora())
    elements.append(Spacer(1, 1))
    elements.append(Paragraph("FORMAS DE PAGAMENTO", subtitle_style))  # MESMO
    elements.append(Spacer(1, 6))
    elements.append(linha_separadora())
    
    # Mapear nomes IGUAL
    nomes_formas = {
        'dinheiro': 'Dinheiro',
        'pix_loja': 'PIX Loja',
        'pix_fabiano': 'PIX Fabiano',
        'pix_edfrance': 'PIX Edfranci',  # MESMO NOME
        'pix_maquineta': 'PIX Maquineta',
        'cartao_debito': 'Cartão Débito',
        'cartao_credito': 'Cartão Crédito',
        'a_prazo': 'A Prazo'
    }
    
    # Exibir formas de pagamento (ORDEM E FORMATO IGUAIS)
    for forma, valor in formas_pagamento.items():
        if valor > 0:
            nome_forma = nomes_formas.get(forma, forma)
            elements.append(linha_dupla(f"{nome_forma}:", moeda_br(valor)))

    # --- Detalhes das Vendas (opcional, manter só se necessário) ---
    # REMOVIDO para ser EXATAMENTE IGUAL à outra rota que não tem esta seção

    # --- Assinaturas (EXATAMENTE IGUAL) ---
    elements.append(Spacer(1, 15))  # MESMO ESPAÇO
    elements.append(linha_separadora())
    elements.append(Paragraph("ASSINATURAS", subtitle_style))  # MESMO
    elements.append(Spacer(1, 6))
    elements.append(linha_separadora())
    elements.append(Spacer(1, 20))  # MESMO
    elements.append(Paragraph("Operador:", normal_style))
    elements.append(Paragraph("____________________________________", normal_style))  # MESMO Nº DE UNDERLINES
    elements.append(Spacer(1, 15))  # MESMO
    elements.append(Paragraph("Administrador:", normal_style))
    elements.append(Paragraph("____________________________________", normal_style))  # MESMO
    
    # NÃO tem rodapé com data/hora (igual à outra rota que não tem)

    # Construir PDF
    doc.build(elements)
    buffer.seek(0)

    # Retornar EXATAMENTE IGUAL
    response = make_response(send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"relatorio_vendas_{data_relatorio.strftime('%Y%m%d')}.pdf"
    ))
    response.headers['Content-Disposition'] = f'inline; filename=relatorio_vendas_{data_relatorio.strftime("%Y%m%d")}.pdf'
    return response
    
# ===== API SALDO =====
@operador_bp.route('/api/saldo', methods=['GET'])
@login_required
@operador_required
def api_get_saldo():
    try:
        # Busca apenas o caixa do operador logado
        caixa = get_caixa_aberto(db.session, operador_id=current_user.id)

        if not caixa:
            logger.info(f"Operador {current_user.nome} tentou acessar saldo sem caixa aberto")
            return jsonify({
                'sucess': False,
                'saldo': 0.00,
                'saldo_formatado': 'R$ 0,00',
                'valor_abertura': 0.00,
                'message': 'Você não possui caixa aberto',
                'caixa_id': None
            })

        # --- Total de VENDAS do dia (entrada, categoria 'venda') ---
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        data_inicio = datetime.combine(hoje, time.min).replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
        data_fim = datetime.combine(hoje, time.max).replace(tzinfo=ZoneInfo('America/Sao_Paulo'))

        # Filtra vendas apenas do caixa do operador atual, excluindo notas canceladas
        lancamentos = db.session.query(Financeiro).join(
            NotaFiscal,
            Financeiro.nota_fiscal_id == NotaFiscal.id,
            isouter=True
        ).filter(
            Financeiro.tipo == TipoMovimentacao.entrada,
            Financeiro.categoria == CategoriaFinanceira.venda,
            Financeiro.data >= data_inicio,
            Financeiro.data <= data_fim,
            Financeiro.caixa_id == caixa.id,
            # Filtro para notas fiscais: ou é nula (não tem nota) ou não está cancelada
            db.or_(
                NotaFiscal.id.is_(None),
                NotaFiscal.status != StatusNota.cancelada
            )
        ).all()

        total_vendas = Decimal('0.00')
        for lanc in lancamentos:
            total_vendas += Decimal(str(lanc.valor))

        # --- Total de DESPESAS do dia ---
        # Busca despesas apenas do caixa do operador atual
        despesas = db.session.query(Financeiro).filter(
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.categoria == CategoriaFinanceira.despesa,
            Financeiro.data >= data_inicio,
            Financeiro.data <= data_fim,
            Financeiro.caixa_id == caixa.id
        ).all()
        
        total_despesas = Decimal('0.00')
        for desp in despesas:
            total_despesas += Decimal(str(desp.valor))

        # --- NOVO: Total em DINHEIRO das vendas do dia ---
        # Busca todas as notas fiscais do dia que não estão canceladas
        notas_dia = db.session.query(NotaFiscal).filter(
            NotaFiscal.caixa_id == caixa.id,
            NotaFiscal.data_emissao >= data_inicio,
            NotaFiscal.data_emissao <= data_fim,
            NotaFiscal.status == StatusNota.emitida
        ).all()

        total_dinheiro = Decimal('0.00')
        
        for nota in notas_dia:
            # Verifica se é uma venda (não é estorno)
            if nota.valor_total > 0:
                # Verifica os pagamentos da nota
                if nota.pagamentos:
                    # Se tem pagamentos múltiplos, soma apenas os em dinheiro
                    for pagamento in nota.pagamentos:
                        if pagamento.forma_pagamento == FormaPagamento.dinheiro:
                            total_dinheiro += Decimal(str(pagamento.valor))
                else:
                    # Se não tem pagamentos múltiplos, verifica a forma de pagamento da nota
                    if nota.forma_pagamento == FormaPagamento.dinheiro:
                        total_dinheiro += Decimal(str(nota.valor_total))

        # --- NOVO: Subtrair estornos de vendas em dinheiro ---
        # Busca estornos (vendas com valor negativo) que foram em dinheiro
        notas_estorno_dinheiro = db.session.query(NotaFiscal).filter(
            NotaFiscal.caixa_id == caixa.id,
            NotaFiscal.data_emissao >= data_inicio,
            NotaFiscal.data_emissao <= data_fim,
            NotaFiscal.status == StatusNota.emitida,
            NotaFiscal.valor_total < 0
        ).all()
        
        for nota_estorno in notas_estorno_dinheiro:
            # Verifica se o estorno foi de uma venda em dinheiro
            if nota_estorno.pagamentos:
                # Se tem pagamentos múltiplos
                for pagamento in nota_estorno.pagamentos:
                    if pagamento.forma_pagamento == FormaPagamento.dinheiro:
                        # Subtrai o valor do estorno (já é negativo, então subtrai valor absoluto)
                        total_dinheiro -= abs(Decimal(str(pagamento.valor)))
            else:
                # Se não tem pagamentos múltiplos
                if nota_estorno.forma_pagamento == FormaPagamento.dinheiro:
                    # Subtrai o valor do estorno (já é negativo, então subtrai valor absoluto)
                    total_dinheiro -= abs(Decimal(str(nota_estorno.valor_total)))

        # --- NOVO: Subtrair despesas em dinheiro ---
        # Busca despesas pagas em dinheiro
        despesas_dinheiro = db.session.query(Financeiro).filter(
            Financeiro.caixa_id == caixa.id,
            Financeiro.data >= data_inicio,
            Financeiro.data <= data_fim,
            Financeiro.tipo == TipoMovimentacao.saida,
            Financeiro.categoria == CategoriaFinanceira.despesa,
            # Busca despesas pagas em dinheiro pelo campo forma_pagamento
            db.or_(
                Financeiro.descricao.ilike('%dinheiro%'),  # Descrição contém "dinheiro"
                # Se tiver um campo específico para forma de pagamento, adicione aqui
            )
        ).all()
        
        for despesa in despesas_dinheiro:
            total_dinheiro -= Decimal(str(despesa.valor))

        # --- Lógica do saldo: abertura + vendas - despesas ---
        abertura = Decimal(str(caixa.valor_abertura))
        saldo = total_vendas - total_despesas

        return jsonify({
            'saldo': float(saldo),
            'saldo_formatado': f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_abertura': float(abertura),
            'total_vendas': float(total_vendas),
            'total_despesas': float(total_despesas),
            'total_dinheiro': float(total_dinheiro),  # NOVO CAMPO
            'total_dinheiro_formatado': f"R$ {total_dinheiro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),  # NOVO CAMPO
            'message': 'Saldo atualizado com sucesso',
            'caixa_id': caixa.id,
            'operador_nome': current_user.nome
        })

    except Exception as e:
        logger.error(f"Erro ao calcular saldo para operador {current_user.nome}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@operador_bp.route('/api/cliente/detalhes/<int:cliente_id>', methods=['GET'])
@login_required
@operador_required
def obter_detalhes_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Obtém todas as contas a receber do cliente
        contas_receber = ContaReceber.query.filter_by(cliente_id=cliente_id).all()
        
        # Obtém todas as notas fiscais do cliente
        notas_fiscais = NotaFiscal.query.filter_by(cliente_id=cliente_id).order_by(NotaFiscal.data_emissao.desc()).all()
        
        # Formata os dados para resposta
        compras = []
        for nota in notas_fiscais:
            conta = next((c for c in contas_receber if c.nota_fiscal_id == nota.id), None)
            compras.append({
                'id': nota.id,
                'data_emissao': nota.data_emissao.isoformat(),
                'valor_total': float(nota.valor_total),
                'a_prazo': nota.a_prazo,
                'valor_pendente': float(conta.valor_aberto) if conta else 0.0,
                'conta_id': conta.id if conta else None
            })
        
        return jsonify({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'documento': cliente.documento,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'endereco': cliente.endereco,
                'limite_credito': float(cliente.limite_credito)
            },
            'saldo_devedor': float(sum(conta.valor_aberto for conta in contas_receber)),
            'compras': compras
        })
    except Exception as e:
        logger.error(f"Erro ao obter detalhes do cliente {cliente_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@operador_bp.route('/api/cliente/registrar-pagamento', methods=['POST'])
@login_required
@operador_required
def registrar_pagamento_cliente():
    try:
        data = request.get_json()
        conta_id = data.get('conta_id')
        nota_fiscal_id = data.get('nota_fiscal_id')
        valor_pago = Decimal(data.get('valor_pago'))
        forma_pagamento = data.get('forma_pagamento')
        observacoes = data.get('observacoes', '')
        
        # Validações
        if not all([conta_id, nota_fiscal_id, valor_pago, forma_pagamento]):
            logger.warning(f"Dados incompletos para registrar pagamento: {data}")
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
            
        conta = ContaReceber.query.get_or_404(conta_id)
        
        if valor_pago <= 0:
            logger.warning(f"Valor de pagamento inválido: {valor_pago}")
            return jsonify({'success': False, 'message': 'Valor deve ser positivo'}), 400
            
        if valor_pago > conta.valor_aberto:
            logger.warning(f"Valor de pagamento excede o devido: {valor_pago} > {conta.valor_aberto}")
            return jsonify({'success': False, 'message': 'Valor excede o devido'}), 400
            
        # Obtém caixa aberto
        caixa = Caixa.query.filter_by(
            operador_id=current_user.id,
            status=StatusCaixa.aberto
        ).first()
        
        if not caixa:
            logger.warning(f"Operador {current_user.nome} tentou registrar pagamento sem caixa aberto")
            return jsonify({'success': False, 'message': 'Nenhum caixa aberto encontrado'}), 400
        
        # Registra pagamento
        conta.registrar_pagamento(
            valor_pago=valor_pago,
            forma_pagamento=forma_pagamento,
            caixa_id=caixa.id,
            observacoes=observacoes
        )
        
        # Cria registro financeiro
        financeiro = Financeiro(
            tipo=TipoMovimentacao.entrada,
            categoria=CategoriaFinanceira.venda,
            valor=valor_pago,
            conta_receber_id=conta.id,
            cliente_id=conta.cliente_id,
            caixa_id=caixa.id,
            descricao=f"Pagamento conta #{conta.id}"
        )
        db.session.add(financeiro)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pagamento registrado com sucesso',
            'novo_saldo': float(conta.valor_aberto)
        })
        
    except Exception as e:
        logger.error(f"Erro ao registrar pagamento para conta {data.get('conta_id')}: {str(e)}", exc_info=True) 
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
        
# ===== API ABERTURA DE CAIXA =====
@operador_bp.route('/api/abrir-caixa', methods=['POST'])
@login_required
@operador_required
def api_abrir_caixa():
    try:
        data = request.get_json()
        valor = Decimal(str(data.get('valor_abertura', 0)))
        
        if valor <= 0:
            logger.warning(f"Operador {current_user.nome} tentou abrir caixa com valor inválido: {valor}")
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
        logger.error(f"Erro ao abrir caixa para operador {current_user.nome}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

# ===== API FECHAMENTO DE CAIXA =====
@operador_bp.route('/api/fechar-caixa', methods=['POST'])
@login_required
@operador_required
def api_fechar_caixa():
    try:
        data = request.get_json()
        
        if 'valor_fechamento' not in data:
            logger.warning(f"Operador {current_user.nome} não forneceu valor_fechamento ao fechar caixa")
            return jsonify({'error': 'Campo valor_fechamento é obrigatório'}), 400
            
        try:
            valor = Decimal(str(data['valor_fechamento']))
        except (TypeError, ValueError, InvalidOperation):
            logger.warning(f"Operador {current_user.nome} forneceu valor_fechamento inválido: {data['valor_fechamento']}")
            return jsonify({'error': 'Valor de fechamento inválido'}), 400
        
        if valor <= 0:
            logger.warning(f"Operador {current_user.nome} tentou fechar caixa com valor_fechamento não positivo: {valor}")
            return jsonify({'error': 'Valor de fechamento deve ser positivo'}), 400
        
        observacao = data.get('observacao', '')

        # Fecha o caixa
        caixa = fechar_caixa(
            db.session,
            current_user.id,
            valor,
            observacao
        )
        
        # Envia o relatório do caixa fechado para o Telegram
        threading.Thread(target=enviar_resumo_caixa_fechado, args=(caixa.id,)).start()
        
        return jsonify({
            'success': True,
            'caixa_id': caixa.id,
            'valor_fechamento': float(valor),
            'observacao': observacao
        })
    
    except Exception as e:
        logger.error(f"Erro ao fechar caixa para operador {current_user.nome}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

# ===== API BUSCAS =====
@operador_bp.route('/api/clientes/buscar', methods=['GET'])
@login_required
@operador_required
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
                'telefone': cliente.telefone,
                'email': cliente.email,
                'endereco': cliente.endereco
            })
    
    return jsonify(resultados)

@operador_bp.route('/api/produtos/buscar', methods=['GET'])
@login_required
@operador_required
def api_buscar_produtos():
    try:
        termo = request.args.get('q', '').lower()
        produtos = get_produtos(db.session)
        
        resultados = []
        for produto in produtos:
            # Verifica se o termo de busca está no nome, marca ou código
            if (termo in produto.nome.lower() or 
                (produto.marca and termo in produto.marca.lower()) or 
                (produto.codigo and termo in produto.codigo.lower())):
                
                estoque_total = produto.estoque_loja + produto.estoque_deposito + produto.estoque_fabrica
                
                resultados.append({
                    'id': produto.id,
                    'nome': produto.nome,
                    'marca': produto.marca,
                    'codigo': produto.codigo,
                    'unidade': produto.unidade.value if produto.unidade else None,
                    'valor_unitario': float(produto.valor_unitario),
                    'estoque_loja': float(produto.estoque_loja),
                    'estoque_deposito': float(produto.estoque_deposito),
                    'estoque_fabrica': float(produto.estoque_fabrica),
                    'estoque_total': float(estoque_total),
                    'descricao': f"{produto.nome} ({produto.marca})" if produto.marca else produto.nome,
                    'disponivel': estoque_total > 0  # Indica se tem estoque disponível
                })
        
        return jsonify(resultados)
    
    except Exception as e:
        logger.error(f"Erro na busca de produtos: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno na busca de produtos'}), 500

@operador_bp.route('/api/usuario', methods=['GET'])
@login_required
@operador_required
def api_get_usuario():
    return jsonify({
        'id': current_user.id,
        'nome': current_user.nome,
        'tipo': current_user.tipo
    })

@operador_bp.route('/api/despesa', methods=['POST'])
@login_required
@operador_required
def registrar_despesa():
    data = request.get_json()

    descricao = data.get("descricao")
    valor = data.get("valor")
    observacao = data.get("observacao")
    caixa_id = data.get("caixa_id")

    if not descricao or not valor or not caixa_id:
        logger.warning(f"Operador {current_user.nome} tentou registrar despesa com dados incompletos: {data}")
        return jsonify({"erro": "Descrição, valor e caixa_id são obrigatórios"}), 400

    try:
        # Pega o horário atual no fuso America/Sao_Paulo (pode ajustar para Fortaleza ou outro)
        agora = datetime.now(ZoneInfo("America/Sao_Paulo"))

        despesa =  Financeiro(
            tipo= TipoMovimentacao.saida,
            categoria= CategoriaFinanceira.despesa,
            valor=Decimal(valor),
            descricao=descricao,
            data=agora, 
            caixa_id=caixa_id,
            sincronizado=False
        )

        if observacao:
            despesa.descricao += f" - Obs: {observacao}"

        db.session.add(despesa)
        db.session.commit()
        logger.info(f"Despesa registrada pelo operador {current_user.nome}: {descricao} - R$ {valor}")
        return jsonify({"mensagem": "Despesa registrada com sucesso"}), 201

    except Exception as e:
        logger.error(f"Erro ao registrar despesa: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500
    
@operador_bp.route('/api/produtos/<int:produto_id>/descontos', methods=['GET'])
@login_required
@operador_required
def api_get_produto_descontos(produto_id):
    try:
        # Busca o produto
        produto = db.session.query( Produto).get(produto_id)
        if not produto:
            logger.warning(f"Produto com ID {produto_id} não encontrado ao buscar descontos")
            return jsonify({'error': 'Produto não encontrado'}), 404
        
        # Busca todos os descontos associados a este produto
        descontos = db.session.query( Desconto)\
            .join( produto_desconto_association)\
            .filter( produto_desconto_association.c.produto_id == produto_id)\
            .all()
        
        # Filtra os descontos ativos e dentro da validade
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).replace(tzinfo=None)  # Remove timezone para comparação
        descontos_validos = []
        
        for desconto in descontos:
            # Verifica se o desconto está ativo
            if not desconto.ativo:
                continue
                
            # Verifica a data limite (se existir)
            if desconto.valido_ate:
                # Remove timezone da data do desconto se existir
                valido_ate = desconto.valido_ate.replace(tzinfo=None) if desconto.valido_ate.tzinfo else desconto.valido_ate
                if valido_ate < hoje:
                    continue  # Desconto expirado
                
            # Adiciona à lista de descontos válidos
            descontos_validos.append({
                'id': desconto.id,
                'identificador': desconto.identificador,
                'tipo': desconto.tipo.value,
                'valor': float(desconto.valor),
                'quantidade_minima': float(desconto.quantidade_minima),
                'quantidade_maxima': float(desconto.quantidade_maxima) if desconto.quantidade_maxima else None,
                'descricao': desconto.descricao,
                'valido_ate': desconto.valido_ate.isoformat() if desconto.valido_ate else None,
                'ativo': desconto.ativo
            })
        
        return jsonify(descontos_validos)
        
    except Exception as e:
        logger.error(f"Erro ao buscar descontos do produto {produto_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao buscar descontos'}), 500
    
@operador_bp.route('/api/clientes/<int:cliente_id>/contas_receber', methods=['GET'])
@login_required
@operador_required
def get_contas_receber_cliente(cliente_id):
    try:
        # Verifica se o cliente existe
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            logger.warning(f"Cliente com ID {cliente_id} não encontrado ao buscar contas a receber")
            return jsonify({'error': 'Cliente não encontrado'}), 404

        # Busca as contas a receber do cliente com os itens da nota fiscal
        contas = ContaReceber.query.filter_by(cliente_id=cliente_id).all()
        
        contas_data = []
        for conta in contas:
            # Busca os itens da nota fiscal associada
            itens_nota = []
            if conta.nota_fiscal:
                for item in conta.nota_fiscal.itens:
                    itens_nota.append({
                        'produto_nome': item.produto.nome if item.produto else 'Produto não encontrado',
                        'quantidade': float(item.quantidade),
                        'unidade_medida': item.produto.unidade.value if item.produto else '',
                        'valor_unitario': float(item.valor_unitario),
                        'valor_total': float(item.valor_total),
                        'desconto_aplicado': float(item.desconto_aplicado) if item.desconto_aplicado else 0.0,
                        'tipo_desconto': item.tipo_desconto.value if item.tipo_desconto else None
                    })
            
            conta_data = {
                'id': conta.id,
                'descricao': conta.descricao,
                'valor_original': float(conta.valor_original),
                'valor_aberto': float(conta.valor_aberto),
                'data_vencimento': conta.data_vencimento.isoformat() if conta.data_vencimento else None,
                'data_emissao': conta.data_emissao.isoformat() if conta.data_emissao else None,
                'data_pagamento': conta.data_pagamento.isoformat() if conta.data_pagamento else None,
                'status': conta.status.value,
                'nota_fiscal_id': conta.nota_fiscal_id,
                'observacoes': conta.observacoes,
                'itens_nota_fiscal': itens_nota,
                'valor_total_nota': float(conta.nota_fiscal.valor_total) if conta.nota_fiscal else 0.0,
                'valor_desconto_nota': float(conta.nota_fiscal.valor_desconto) if conta.nota_fiscal and conta.nota_fiscal.valor_desconto else 0.0,
                'tipo_desconto_nota': conta.nota_fiscal.tipo_desconto.value if conta.nota_fiscal and conta.nota_fiscal.tipo_desconto else None
            }
            contas_data.append(conta_data)

        return jsonify(contas_data)

    except Exception as e:
        logger.error(f"Erro ao buscar contas a receber do cliente {cliente_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

from flask import make_response
from reportlab.lib.pagesizes import A4, mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from datetime import datetime
import os

@operador_bp.route('/api/contas_receber/<int:conta_id>/comprovante', methods=['GET'])
@login_required
@operador_required
def gerar_comprovante_conta(conta_id):
    try:
        # Busca a conta a receber
        conta = ContaReceber.query.get(conta_id)
        if not conta:
            logger.warning(f"Conta a receber com ID {conta_id} não encontrada para gerar comprovante")
            return jsonify({'error': 'Conta não encontrada'}), 404
        
        # Busca informações do cliente
        cliente = conta.cliente
        
        # Busca pagamentos realizados
        pagamentos = PagamentoContaReceber.query.filter_by(conta_id=conta_id).all()
        
        # Cria o PDF em memória
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(80*mm, 297*mm))  # Bobina 80mm
        
        # Configurações
        width, height = 80*mm, 297*mm
        margin = 5*mm
        y_position = height - margin
        
        # Adiciona imagem no topo totalmente colada (sem margem superior)
        logo_path = os.path.join('app', 'static', 'assets', 'logo.jpeg')
        if os.path.exists(logo_path):
            try:
                logo = ImageReader(logo_path)
                # Imagem colada no topo sem margem
                c.drawImage(logo, 0, height - 20*mm, width=80*mm, height=20*mm, 
                           preserveAspectRatio=True, anchor='n')
                y_position = height - 25*mm  # Ajusta a posição Y após a imagem
            except Exception as e:
                # Se houver erro, continua sem a imagem
                y_position -= 5*mm
        else:
            # Se não encontrar a imagem, ajusta o posicionamento
            y_position = height - 10*mm
        
        # Função para adicionar texto com quebra de linha
        def add_text(text, x, y, max_width, font_size=9, font_name="Helvetica"):
            c.setFont(font_name, font_size)
            lines = []
            words = text.split()
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                if c.stringWidth(test_line, font_name, font_size) <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                c.drawString(x, y, line)
                y -= font_size + 2
            
            return y
        
        # Função para adicionar linha separadora
        def add_separator(y):
            c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
            c.line(margin, y, width - margin, y)
            c.setStrokeColorRGB(0, 0, 0)  # Volta para preto
            return y - 5
        
        # Cabeçalho
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, y_position, "COMPROVANTE DE DÉDITO")
        y_position -= 15
        
        c.setFont("Helvetica", 9)
        c.drawString(margin, y_position, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y_position -= 12
        
        # Linha separadora
        y_position = add_separator(y_position)
        
        # Informações do Cliente
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y_position, "CLIENTE:")
        y_position -= 12
        
        c.setFont("Helvetica", 9)
        y_position = add_text(f"{cliente.nome}", margin, y_position, width - 2*margin)
        if cliente.documento:
            y_position = add_text(f"Doc: {cliente.documento}", margin, y_position, width - 2*margin)
        if cliente.telefone:
            y_position = add_text(f"Tel: {cliente.telefone}", margin, y_position, width - 2*margin)
        
        y_position -= 8
        
        # Linha separadora
        y_position = add_separator(y_position)
        
        # Informações da Conta
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y_position, "DÉBITO:")
        y_position -= 12
        
        c.setFont("Helvetica", 9)
        y_position = add_text(f"Descrição: {conta.descricao}", margin, y_position, width - 2*margin)
        y_position = add_text(f"Valor Original: R$ {format_number(conta.valor_original)}", margin, y_position, width - 2*margin)
        y_position = add_text(f"Valor Aberto: R$ {format_number(conta.valor_aberto)}", margin, y_position, width - 2*margin)
        y_position = add_text(f"Vencimento: {conta.data_vencimento.strftime('%d/%m/%Y')}", margin, y_position, width - 2*margin)
        
        if conta.data_pagamento:
            y_position = add_text(f"Data Pagamento: {conta.data_pagamento.strftime('%d/%m/%Y %H:%M')}", margin, y_position, width - 2*margin)
        
        # Status com destaque
        status_color = (0, 0.5, 0) if conta.status.value.upper() == "PAGO" else (0.8, 0, 0)  # Verde para pago, vermelho para outros
        c.setFillColorRGB(*status_color)
        y_position = add_text(f"Status: {conta.status.value.upper()}", margin, y_position, width - 2*margin)
        c.setFillColorRGB(0, 0, 0)  # Volta para preto
        
        y_position -= 8
        
        # Linha separadora
        y_position = add_separator(y_position)
        
        # Itens da Nota Fiscal (se existir)
        if conta.nota_fiscal and conta.nota_fiscal.itens:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, y_position, "PRODUTOS:")
            y_position -= 12
            
            c.setFont("Helvetica", 8)
            for item in conta.nota_fiscal.itens:
                produto_text = f"{item.produto.nome if item.produto else 'Produto'}"
                y_position = add_text(produto_text, margin, y_position, width - 2*margin, 8)

                detalhes = f"{item.quantidade:.2f} {item.produto.unidade.value if item.produto else 'un'} x R$ {format_number(item.valor_unitario)}"
                if item.desconto_aplicado and item.desconto_aplicado > 0:
                    detalhes += f" (-R$ {format_number(item.desconto_aplicado)})"
                
                detalhes += f" = R$ {format_number(item.valor_total)}"
                
                y_position = add_text(detalhes, margin + 5*mm, y_position, width - 7*margin, 8)
                y_position -= 4
            
            # Total da nota
            y_position -= 4
            c.setFont("Helvetica-Bold", 9)
            total_text = f"TOTAL NOTA: R$ {format_number(conta.nota_fiscal.valor_total)}"
            c.drawString(margin, y_position, total_text)
            y_position -= 12
            
            # Linha separadora
            y_position = add_separator(y_position)
        
        # Pagamentos Realizados
        if pagamentos:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, y_position, "PAGAMENTOS:")
            y_position -= 12
            
            c.setFont("Helvetica", 8)
            total_pago = 0
            for pagamento in pagamentos:
                pag_text = f"{pagamento.data_pagamento.strftime('%d/%m/%Y')} - R$ {format_number(pagamento.valor_pago)}"
                pag_text += f" ({pagamento.forma_pagamento.value})"
                
                y_position = add_text(pag_text, margin, y_position, width - 2*margin, 8)
                total_pago += pagamento.valor_pago
            
            y_position -= 4
            c.setFont("Helvetica-Bold", 9)
            c.drawString(margin, y_position, f"TOTAL PAGO: R$ {format_number(total_pago)}")
            y_position -= 12
            
            # Linha separadora
            y_position = add_separator(y_position)
        
        # Observações
        if conta.observacoes:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(margin, y_position, "OBSERVAÇÕES:")
            y_position -= 10
            
            c.setFont("Helvetica", 8)
            y_position = add_text(conta.observacoes, margin, y_position, width - 2*margin, 8)
            y_position -= 8
        
        # Finaliza o PDF
        c.showPage()
        c.save()
        
        buffer.seek(0)
        
        # Retorna o PDF como resposta
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=comprovante_conta_{conta_id}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar comprovante para conta {conta_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@operador_bp.route('/api/clientes/<int:cliente_id>/notas_fiscais', methods=['GET'])
@login_required
@operador_required
def get_notas_fiscais_cliente(cliente_id):
    try:
        # Verifica se o cliente existe
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            logger.warning(f"Cliente com ID {cliente_id} não encontrado ao buscar notas fiscais")
            return jsonify({'error': 'Cliente não encontrado'}), 404

        # Busca as notas fiscais do cliente
        notas = NotaFiscal.query.filter_by(cliente_id=cliente_id).order_by(NotaFiscal.data_emissao.desc()).all()
        
        notas_data = []
        for nota in notas:
            notas_data.append({
                'id': nota.id,
                'data_emissao': nota.data_emissao.isoformat() if nota.data_emissao else None,
                'valor_total': float(nota.valor_total),
                'valor_desconto': float(nota.valor_desconto),
                'status': nota.status.value,
                'a_prazo': nota.a_prazo,
                'forma_pagamento': nota.forma_pagamento.value if nota.forma_pagamento else None,
                'valor_recebido': float(nota.valor_recebido) if nota.valor_recebido else None,
                'troco': float(nota.troco) if nota.troco else None,
                'operador_id': nota.operador_id,
                'caixa_id': nota.caixa_id
            })
        
        return jsonify(notas_data)

    except Exception as e:
        logger.error(f"Erro ao buscar notas fiscais do cliente {cliente_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@operador_bp.route('/api/contas_receber/<int:conta_id>/pagamento', methods=['POST'])
@login_required
@operador_required
def registrar_pagamento_conta(conta_id):
    try:
        data = request.get_json()
        valor_pago = Decimal(data.get('valor_pago'))
        forma_pagamento = data.get('forma_pagamento')
        observacoes = data.get('observacoes', '').strip()
        
        # Verifica se a conta existe
        conta = ContaReceber.query.get(conta_id)
        if not conta:
            logger.warning(f"Conta a receber com ID {conta_id} não encontrada ao registrar pagamento")
            return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
        
        # Validações
        if valor_pago <= 0:
            logger.warning(f"Valor de pagamento inválido: {valor_pago} para conta {conta_id}")
            return jsonify({'success': False, 'message': 'Valor do pagamento deve ser positivo'}), 400
            
        if valor_pago > conta.valor_aberto:
            logger.warning(f"Valor de pagamento excede o valor em aberto: {valor_pago} > {conta.valor_aberto} para conta {conta_id}")
            return jsonify({'success': False, 'message': 'Valor do pagamento excede o valor em aberto'}), 400
            
        if not forma_pagamento:
            logger.warning(f"Forma de pagamento não informada para conta {conta_id}")
            return jsonify({'success': False, 'message': 'Forma de pagamento não informada'}), 400
        
        # Obtém o caixa aberto do operador atual
        caixa_aberto = Caixa.query.filter_by(
            operador_id=current_user.id,
            status=StatusCaixa.aberto
        ).order_by(Caixa.data_abertura.desc()).first()
        
        if not caixa_aberto:
            logger.warning(f"Operador {current_user.nome} tentou registrar pagamento sem caixa aberto para conta {conta_id}")
            return jsonify({'success': False, 'message': 'Nenhum caixa aberto encontrado para o operador'}), 400
        
        # Registra o pagamento
        conta.registrar_pagamento(
            valor_pago=valor_pago,
            forma_pagamento=FormaPagamento(forma_pagamento),
            caixa_id=caixa_aberto.id,
            observacoes=observacoes
        )
        
        db.session.commit()
        logger.info(f"Pagamento de R$ {valor_pago} registrado para conta {conta_id} pelo operador {current_user.nome}")
        return jsonify({
            'success': True,
            'message': 'Pagamento registrado com sucesso',
            'novo_status': conta.status.value,
            'valor_aberto': float(conta.valor_aberto)
        })
        
    except Exception as e:
        logger.error(f"Erro ao registrar pagamento para conta {conta_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao registrar pagamento: {str(e)}'}), 500

@operador_bp.route('/api/clientes/<int:cliente_id>', methods=['GET'])
@login_required
@operador_required
def get_cliente(cliente_id):
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            logger.warning(f"Cliente com ID {cliente_id} não encontrado")
            return jsonify({'error': 'Cliente não encontrado'}), 404
            
        return jsonify({
            'id': cliente.id,
            'nome': cliente.nome,
            'documento': cliente.documento,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': cliente.endereco,
            'limite_credito': float(cliente.limite_credito) if cliente.limite_credito else None,
            'ativo': cliente.ativo,
            'criado_em': cliente.criado_em.isoformat() if cliente.criado_em else None
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar cliente {cliente_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
# ================ ORÇAMENTO ====================
@operador_bp.route('/api/orcamento/pdf', methods=['POST'])
@login_required
@operador_required
def gerar_pdf_orcamento():
    try:
        from reportlab.lib.pagesizes import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from flask import request, jsonify, make_response
        from io import BytesIO
        from datetime import datetime
        import os

        dados = request.get_json()
        if not dados or 'itens' not in dados or not dados['itens']:
            logger.warning(f"Dados do orçamento inválidos: {dados}")
            return jsonify({'success': False, 'message': 'Dados do orçamento inválidos'}), 400

        buffer = BytesIO()
        # Margens zeradas no topo e laterais para imagem colada no topo
        doc = SimpleDocTemplate(buffer, pagesize=(80*mm, 250*mm), 
                              rightMargin=0, leftMargin=0,
                              topMargin=-6, bottomMargin=10*mm)
        elements = []

        styles = getSampleStyleSheet()
        style_normal = ParagraphStyle('normal', parent=styles['Normal'], 
                                     fontName='Helvetica', fontSize=10, leading=10)
        style_centered = ParagraphStyle('centered', parent=style_normal, alignment=1)
        style_right = ParagraphStyle('right', parent=style_normal, alignment=2)
        style_bold = ParagraphStyle('bold', parent=style_normal, fontName='Helvetica-Bold')
        style_italic = ParagraphStyle('italic', parent=style_normal, 
                                     fontName='Helvetica-Oblique', fontSize=10)
        style_title = ParagraphStyle('title', parent=style_bold, 
                                   fontSize=14, alignment=1, spaceAfter=10)

        # Imagem no topo totalmente colada (sem margem superior)
        logo_path = os.path.join('app', 'static', 'assets', 'logo.jpeg')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=80*mm, height=20*mm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                # Espaçamento mínimo após a imagem
                elements.append(Spacer(1, 2))
            except Exception as e:
                logger.error(f"Erro ao carregar imagem: {e}")

        # Cabeçalho
        elements.append(Paragraph("ORÇAMENTO", style_title))
        elements.append(Paragraph(f"Contato: (87) 9 8152-1788", style_centered))
        elements.append(Paragraph(f"Av. Fernando Bezerra, 123 - Centro - Ouricuri-PE", style_centered))
        elements.append(Spacer(1, 18))
        elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_centered))
        
        if dados.get('cliente'):
            cliente = dados['cliente']
            elements.append(Paragraph(f"Cliente: {cliente.get('nome', 'CONSUMIDOR FINAL')}", style_centered))
            if cliente.get('documento'):
                elements.append(Paragraph(f"Documento: {cliente['documento']}", style_centered))
        
        elements.append(Spacer(1, 18))

        # Tabela de itens
        table_data = [[
            Paragraph("<b>Descrição</b>", style_centered),
            Paragraph("<b>Qtd</b>", style_centered),
            Paragraph("<b>Unitário R$</b>", style_centered),
            Paragraph("<b>Total R$</b>", style_centered)
        ]]

        subtotal = 0
        desconto_total = 0
        for item in dados['itens']:
            descricao = item.get('nome', 'Produto sem nome')
            qtd = float(item.get('quantidade', 1))
            valor_unitario = float(item.get('valor_unitario', 0))
            valor_total = float(item.get('valor_total', qtd * valor_unitario))
            desconto_item = float(item.get('valor_desconto', 0))

            table_data.append([
                Paragraph(descricao, style_normal),
                Paragraph(f"{qtd:.1f}".replace('.', ','), style_right),
                Paragraph(f"{format_currency(valor_unitario)}".replace('.', ','), style_right),
                Paragraph(f"{format_currency(valor_total)}".replace('.', ','), style_right)
            ])

            if desconto_item > 0:
                table_data.append([
                    Paragraph(f"Desconto: R$ {desconto_item:.2f}".replace('.', ','), style_italic), 
                    '', '', ''])

            subtotal += valor_total
            desconto_total += desconto_item

        col_widths = [30*mm, 12*mm, 17*mm, 17*mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F5F5F5')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8))

        # Totais
        total = subtotal
        elements.append(Paragraph(f"Subtotal: R$ {format_currency(subtotal)}".replace('.', ','), style_right))
        if desconto_total > 0:
            elements.append(Paragraph(f"Descontos: -R$ {format_currency(desconto_total)}".replace('.', ','), style_right))
        elements.append(Paragraph(f"<b>TOTAL: R$ {format_currency(total)}</b>".replace('.', ','), style_right))
        elements.append(Spacer(1, 10))
        
        elements.append(
            Paragraph(
                f"Orçamento válido somente até hoje.",
                style_centered
            )
        )
        
        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=orcamento.pdf'
        return response

    except Exception as e:
        logger.error(f"Erro ao gerar PDF do orçamento: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao gerar PDF: {str(e)}'}), 500