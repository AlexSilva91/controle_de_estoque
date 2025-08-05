import base64
from functools import wraps
from io import BytesIO
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
from app.bot.bot_movimentacao import enviar_resumo_movimentacao_diaria
from flask import send_file
from app.utils.preparar_notas import preparar_dados_nota
from app.utils.converter_endereco import parse_endereco_string
from app.utils.nfce import gerar_nfce_pdf_bobina_bytesio
from app.models import entities
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

operador_bp = Blueprint('operador', __name__, url_prefix='/operador')

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
    return render_template('dashboard_operador.html', nome_usuario=current_user.nome)

# ===== API CLIENTES =====
@operador_bp.route('/api/clientes', methods=['GET'])
@login_required
@operador_required
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
@operador_required
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
@operador_required
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
@operador_required
def api_delete_cliente(cliente_id):
    try:
        success = delete_cliente(db.session, cliente_id)
        return jsonify({'success': success}), 200
    except ValueError as e:
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
        app.logger.error(f"Erro ao obter produtos: {str(e)}", exc_info=True)
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
        
        return jsonify({'error': 'Produto não encontrado'}), 404
    
    except Exception as e:
        app.logger.error(f"Erro ao obter produto ID {produto_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao buscar produto'}), 500

# ===== API VENDAS =====
@operador_bp.route('/api/vendas', methods=['POST'])
@login_required
@operador_required
def api_registrar_venda():
    # Verificação inicial do conteúdo da requisição
    if not request.is_json:
        app.logger.error("Requisição sem cabeçalho Content-Type: application/json")
        return jsonify({
            'success': False,
            'message': 'Content-Type deve ser application/json'
        }), 400

    try:
        dados_venda = request.get_json()
        if dados_venda is None:
            app.logger.error("Nenhum dado JSON recebido ou JSON inválido")
            return jsonify({
                'success': False,
                'message': 'JSON inválido ou não enviado'
            }), 400

        app.logger.info(f"Dados recebidos: {dados_venda}")

        # Campos obrigatórios
        required_fields = ['cliente_id', 'itens', 'pagamentos', 'valor_total']
        for field in required_fields:
            if field not in dados_venda:
                app.logger.error(f"Campo obrigatório faltando: {field}")
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório faltando: {field}'
                }), 400

        # Validação de tipos
        if not isinstance(dados_venda['itens'], list) or len(dados_venda['itens']) == 0:
            app.logger.error("Lista de itens inválida ou vazia")
            return jsonify({
                'success': False,
                'message': 'Lista de itens inválida ou vazia'
            }), 400

        if not isinstance(dados_venda['pagamentos'], list) or len(dados_venda['pagamentos']) == 0:
            app.logger.error("Lista de pagamentos inválida ou vazia")
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
            app.logger.error(f"Erro na conversão de valores: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Valores numéricos inválidos'
            }), 400

        # Consultar cliente
        cliente = entities.Cliente.query.get(cliente_id)
        if not cliente:
            app.logger.error(f"Cliente não encontrado: ID {cliente_id}")
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
                    app.logger.error(f"Produto não encontrado: ID {produto_id}")
                    return jsonify({
                        'success': False,
                        'message': f'Produto não encontrado: ID {produto_id}'
                    }), 404

            except (ValueError, InvalidOperation, TypeError) as e:
                app.logger.error(f"Erro ao processar item: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Dados do item inválidos'
                }), 400

        # Verificar soma dos pagamentos
        try:
            soma_pagamentos = sum(Decimal(str(p.get('valor'))) for p in dados_venda['pagamentos'])
            a_prazo_usado = any(p.get('forma_pagamento') == 'a_prazo' for p in dados_venda['pagamentos'])
            
            # Verifica se a soma dos pagamentos bate com o valor total
            if abs(soma_pagamentos - valor_total) > Decimal('0.01'):
                msg = f'Valor recebido ({soma_pagamentos}) diferente do total da venda ({valor_total})'
                app.logger.error(msg)
                return jsonify({
                    'success': False,
                    'message': msg
                }), 400
        except (ValueError, InvalidOperation, TypeError) as e:
            app.logger.error(f"Erro ao verificar pagamentos: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Dados de pagamento inválidos'
            }), 400

        # Verificar caixa aberto
        caixa_aberto = entities.Caixa.query.filter_by(status='aberto').first()
        if not caixa_aberto:
            app.logger.error("Nenhum caixa aberto encontrado")
            return jsonify({
                'success': False,
                'message': 'Nenhum caixa aberto encontrado'
            }), 400

        # Criar registro de Nota Fiscal
        nota = entities.NotaFiscal(
            cliente_id=cliente.id,
            operador_id=current_user.id,
            caixa_id=caixa_aberto.id,
            data_emissao=datetime.utcnow(),
            valor_total=valor_total,
            valor_desconto=total_descontos,
            tipo_desconto=None,
            status=entities.StatusNota.emitida,
            forma_pagamento=entities.FormaPagamento.dinheiro,  # Será atualizado abaixo
            valor_recebido=valor_recebido,
            troco=max(valor_recebido - valor_total, Decimal(0)) if not a_prazo_usado else Decimal(0),
            a_prazo=a_prazo_usado
        )

        # Criar Entrega, se presente - COM TRATAMENTO SEGURO
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
            
            # Tratamento seguro para desconto_info
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
            
            # Atualizar estoque
            produto.estoque_loja -= quantidade

        # Criar pagamentos e armazenar seus IDs
        pagamentos_ids = []
        valor_a_prazo = Decimal(0)
        
        for pagamento_data in dados_venda['pagamentos']:
            forma = pagamento_data.get('forma_pagamento')
            valor = Decimal(str(pagamento_data.get('valor')))
            
            pagamento_nf = entities.PagamentoNotaFiscal(
                nota_fiscal_id=nota.id,
                forma_pagamento=entities.FormaPagamento(forma),
                valor=valor,
                data=datetime.utcnow(),
                sincronizado=False
            )
            db.session.add(pagamento_nf)
            db.session.flush()  # Garante que teremos o ID do pagamento
            
            pagamentos_ids.append(pagamento_nf.id)
            
            # Registrar no financeiro APENAS se não for a prazo
            if forma != 'a_prazo':
                financeiro = entities.Financeiro(
                    tipo=entities.TipoMovimentacao.entrada,
                    categoria=entities.CategoriaFinanceira.venda,
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
            conta_receber = entities.ContaReceber(
                cliente_id=cliente.id,
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo NF #{nota.id}",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=datetime.utcnow() + timedelta(days=30),
                status=entities.StatusPagamento.pendente,
                sincronizado=False
            )
            db.session.add(conta_receber)

        # Atualizar a forma de pagamento principal da nota fiscal
        if len(dados_venda['pagamentos']) == 1:
            # Se houver apenas um pagamento, usa essa forma
            nota.forma_pagamento = entities.FormaPagamento(dados_venda['pagamentos'][0]['forma_pagamento'])
        else:
            # Se houver múltiplos pagamentos, define como "misto"
            nota.forma_pagamento = entities.FormaPagamento.dinheiro  # Ou criar um enum para "misto"

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
        app.logger.error(f'Erro no banco ao registrar venda: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Erro ao registrar venda no banco',
            'error': str(e)
        }), 500
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro inesperado ao registrar venda: {str(e)}', exc_info=True)
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
        print(dados_nota)
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
        app.logger.error(f"Erro ao gerar PDF: {str(e)}")
        abort(500, description="Ocorreu um erro ao gerar o PDF")


@operador_bp.route('/api/vendas/hoje', methods=['GET'])
@login_required
@operador_required
def obter_vendas_hoje():
    try:
        # Obtém parâmetros de filtro
        data_str = request.args.get('data')
        caixa_id = request.args.get('caixa_id', type=int)
        operador_id = request.args.get('operador_id', type=int)
        
        # Converte a data se fornecida
        data = None
        if data_str:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Obtém as vendas (agora já filtradas por caixas abertos)
        vendas = entities.NotaFiscal.obter_vendas_do_dia(
            data=data,
            caixa_id=caixa_id,
            operador_id=operador_id
        )
        
        # Formata a resposta (mantém o mesmo formato anterior)
        vendas_formatadas = []
        for venda in vendas:
            vendas_formatadas.append({
                'id': venda.id,
                'data_emissao': venda.data_emissao.isoformat(),
                'cliente': {
                    'id': venda.cliente.id if venda.cliente else None,
                    'nome': venda.cliente.nome if venda.cliente else 'Consumidor Final'
                },
                'operador': {
                    'id': venda.operador.id,
                    'nome': venda.operador.nome
                },
                'caixa': {
                    'id': venda.caixa.id,
                    'status': venda.caixa.status.value,
                    'valor_abertura': float(venda.caixa.valor_abertura)
                },
                'valor_total': float(venda.valor_total),
                'valor_desconto': float(venda.valor_desconto),
                'forma_pagamento': venda.forma_pagamento.value if venda.forma_pagamento else None,
                'a_prazo': venda.a_prazo,
                'itens': [
                    {
                        'produto_id': item.produto.id,
                        'produto_nome': item.produto.nome,
                        'quantidade': float(item.quantidade),
                        'valor_unitario': float(item.valor_unitario),
                        'valor_total': float(item.valor_total),
                        'desconto_aplicado': float(item.desconto_aplicado) if item.desconto_aplicado else None
                    }
                    for item in venda.itens
                ],
                'pagamentos': [
                    {
                        'forma_pagamento': pagamento.forma_pagamento.value,
                        'valor': float(pagamento.valor),
                        'data': pagamento.data.isoformat()
                    }
                    for pagamento in venda.pagamentos
                ] if venda.pagamentos else None
            })
        
        return jsonify({
            'success': True,
            'data': vendas_formatadas,
            'total_vendas': len(vendas),
            'total_valor': sum(float(v.valor_total) for v in vendas)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter vendas do dia: {str(e)}'
        }), 500

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
        total_vendas = db.session.query(func.count(entities.NotaFiscal.id)).join(
            entities.Caixa,
            entities.NotaFiscal.caixa_id == entities.Caixa.id
        ).filter(
            entities.NotaFiscal.data_emissao >= inicio_dia,
            entities.NotaFiscal.data_emissao <= fim_dia,
            entities.NotaFiscal.status == StatusNota.emitida,
            entities.Caixa.status == StatusCaixa.aberto  # Filtro por caixas abertos
        ).scalar()
        
        # Valor total vendido (apenas em caixas abertos)
        valor_total = db.session.query(func.coalesce(func.sum(entities.NotaFiscal.valor_total), 0)).join(
            entities.Caixa,
            entities.NotaFiscal.caixa_id == entities.Caixa.id
        ).filter(
            entities.NotaFiscal.data_emissao >= inicio_dia,
            entities.NotaFiscal.data_emissao <= fim_dia,
            entities.NotaFiscal.status == StatusNota.emitida,
            entities.Caixa.status == StatusCaixa.aberto  # Filtro por caixas abertos
        ).scalar()
        
        # Formas de pagamento (apenas em caixas abertos)
        formas_pagamento = db.session.query(
            entities.NotaFiscal.forma_pagamento,
            func.count(entities.NotaFiscal.id).label('quantidade'),
            func.sum(entities.NotaFiscalotaFiscal.valor_total).label('valor_total')
        ).join(
            entities.Caixa,
            entities.NotaFiscal.caixa_id == entities.Caixa.id
        ).filter(
            entities.NotaFiscal.data_emissao >= inicio_dia,
            entities.NotaFiscal.data_emissao <= fim_dia,
            entities.NotaFiscal.status == StatusNota.emitida,
            entities.Caixa.status == StatusCaixa.aberto  # Filtro por caixas abertos
        ).group_by(entities.NotaFiscal.forma_pagamento).all()
        
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
        nota_fiscal = entities.NotaFiscal.query.get_or_404(venda_id)
        
        # Busca os pagamentos associados
        pagamentos = entities.PagamentoNotaFiscal.query.filter_by(
            nota_fiscal_id=venda_id
        ).all()
        
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
                for pagamento in pagamentos
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
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
            
        motivo_estorno = dados.get('motivo_estorno')
        if not motivo_estorno:
            return jsonify({'success': False, 'message': 'Motivo do estorno é obrigatório'}), 400
            
        usuario_id = current_user.id
        
        resultado = estornar_venda(db, sale_id, motivo_estorno, usuario_id)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar venda {sale_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno ao processar estorno'
        }), 500
        
@operador_bp.route('/api/vendas/relatorio-diario-pdf', methods=['GET'])
@login_required
@operador_required
def gerar_pdf_vendas_dia():
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    from io import BytesIO
    from flask import send_file, request, jsonify
    from datetime import datetime

    data_str = request.args.get('data')
    caixa_id = request.args.get('caixa_id')
    operador_id = request.args.get('operador_id')
    data = None

    if data_str:
        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    resultado = obter_detalhes_vendas_dia(data, caixa_id, operador_id)
    if not resultado['success']:
        return jsonify(resultado), 400

    dados = resultado['data']
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    linha_atual = height - margin
    espacamento = 20
    espacamento_pequeno = 12

    def verificar_espaco(altura_necessaria):
        nonlocal linha_atual, pdf
        if linha_atual - altura_necessaria < margin:
            pdf.showPage()
            linha_atual = height - margin
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(margin, linha_atual, "RELATÓRIO DIÁRIO DETALHADO DE VENDAS (CONTINUAÇÃO)")
            linha_atual -= espacamento * 1.5

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, linha_atual, "RELATÓRIO DIÁRIO DETALHADO DE VENDAS")
    linha_atual -= espacamento * 1.5

    data_relatorio = data if data else datetime.now().date()
    pdf.setFont("Helvetica", 12)
    pdf.drawString(margin, linha_atual, f"Data: {data_relatorio.strftime('%d/%m/%Y')}")
    linha_atual -= espacamento_pequeno

    if caixa_id:
        pdf.drawString(margin, linha_atual, f"Caixa ID: {caixa_id}")
        linha_atual -= espacamento_pequeno
    if operador_id:
        pdf.drawString(margin, linha_atual, f"Operador ID: {operador_id}")
        linha_atual -= espacamento_pequeno

    linha_atual -= espacamento

    total_vendas_positivas = sum(v['valor_total'] for v in dados['vendas'] if v['valor_total'] > 0)
    total_estornos = sum(abs(v['valor_total']) for v in dados['vendas'] if v['valor_total'] < 0)
    total_liquido = total_vendas_positivas - total_estornos

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin, linha_atual, "RESUMO FINANCEIRO")
    linha_atual -= espacamento

    dados_resumo = [
        ["Total de Vendas:", f"R$ {total_vendas_positivas:.2f}"],
        ["Total de Estornos:", f"R$ {total_estornos:.2f}"],
        ["Total de Descontos:", f"R$ {dados['total_descontos']:.2f}"],
        ["Total de Entradas:", f"R$ {dados['total_entradas']:.2f}"],
        ["Total de Saídas:", f"R$ {dados['total_saidas']:.2f}"],
        ["Saldo Líquido:", f"R$ {total_liquido:.2f}"]
    ]

    tabela_resumo = Table(dados_resumo, colWidths=[180, 120])
    tabela_resumo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('TEXTCOLOR', (0, 1), (1, 1), colors.red),
        ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
    ]))

    altura_resumo = tabela_resumo.wrap(width - 2 * margin, height)[1]
    verificar_espaco(altura_resumo)
    tabela_resumo.drawOn(pdf, margin, linha_atual - altura_resumo)
    linha_atual -= altura_resumo + espacamento

    for venda in dados['vendas']:
        is_estorno = venda['valor_total'] < 0
        valor_exibicao = abs(venda['valor_total'])

        pdf.setFont("Helvetica-Bold", 14)
        if is_estorno:
            pdf.setFillColor(colors.red)
            pdf.drawString(margin, linha_atual, f"ESTORNO DA VENDA #{venda['id']}")
            pdf.setFillColor(colors.black)
        else:
            pdf.drawString(margin, linha_atual, f"DETALHES DA VENDA #{venda['id']}")
        linha_atual -= espacamento

        info_venda = [
            ["Cliente:", venda['cliente']],
            ["Data/Hora:", datetime.fromisoformat(venda['data']).strftime('%d/%m/%Y %H:%M')],
            ["Operador:", venda['operador']],
            ["Valor Total:", f"R$ {valor_exibicao:.2f}"],
            ["Desconto:", f"R$ {venda['valor_desconto']:.2f}"],
            ["Forma Pagamento:", venda['forma_pagamento']],
            ["A Prazo:", "Sim" if venda['a_prazo'] else "Não"],
            ["Tipo:", "ESTORNO" if is_estorno else "VENDA NORMAL"]
        ]

        tabela_info = Table(info_venda, colWidths=[100, 300])
        estilo_info = [
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey)
        ]
        if is_estorno:
            estilo_info.append(('TEXTCOLOR', (0, 7), (1, 7), colors.red))
            estilo_info.append(('FONTNAME', (0, 7), (1, 7), 'Helvetica-Bold'))

        tabela_info.setStyle(TableStyle(estilo_info))
        altura_info = tabela_info.wrap(width - 2 * margin, height)[1]
        verificar_espaco(altura_info)
        tabela_info.drawOn(pdf, margin, linha_atual - altura_info)
        linha_atual -= altura_info + espacamento

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, linha_atual, "ITENS:")
        linha_atual -= espacamento_pequeno

        dados_itens = [["Produto", "Qtd", "V. Unit.", "V. Total", "Desconto"]]
        for item in venda['itens']:
            quantidade = -item['quantidade'] if is_estorno else item['quantidade']
            valor_total = -item['valor_total'] if is_estorno else item['valor_total']
            desconto = -item['desconto'] if is_estorno and item['desconto'] else item['desconto']
            dados_itens.append([
                item['produto'],
                f"{quantidade:.3f}",
                f"R$ {item['valor_unitario']:.2f}",
                f"R$ {valor_total:.2f}",
                f"R$ {desconto:.2f}" if desconto > 0 else "-"
            ])

        tabela_itens = Table(dados_itens, colWidths=[180, 50, 70, 70, 60])
        estilo_itens = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]
        if is_estorno:
            estilo_itens.append(('TEXTCOLOR', (0, 1), (-1, -1), colors.red))

        tabela_itens.setStyle(TableStyle(estilo_itens))
        altura_itens = tabela_itens.wrap(width - 2 * margin, height)[1]
        verificar_espaco(altura_itens)
        tabela_itens.drawOn(pdf, margin, linha_atual - altura_itens)
        linha_atual -= altura_itens + espacamento

        # linha separadora entre vendas
        pdf.setStrokeColor(colors.lightgrey)
        pdf.line(margin, linha_atual, width - margin, linha_atual)
        linha_atual -= espacamento

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,
        download_name=f"relatorio_vendas_{data_relatorio.strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

    
# ===== API SALDO =====
@operador_bp.route('/api/saldo', methods=['GET'])
@login_required
@operador_required
def api_get_saldo():
    try:
        caixa = get_caixa_aberto(db.session)

        if not caixa:
            return jsonify({
                'saldo': 0.00,
                'saldo_formatado': 'R$ 0,00',
                'valor_abertura': 0.00,
                'message': 'Nenhum caixa aberto encontrado'
            })

        # --- Total de VENDAS do dia (entrada, categoria 'venda') ---
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        data_inicio = datetime.combine(hoje, time.min).replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
        data_fim = datetime.combine(hoje, time.max).replace(tzinfo=ZoneInfo('America/Sao_Paulo'))

        lancamentos = db.session.query(entities.Financeiro).filter(
            entities.Financeiro.tipo == entities.TipoMovimentacao.entrada,
            entities.Financeiro.categoria == entities.CategoriaFinanceira.venda,
            entities.Financeiro.data >= data_inicio,
            entities.Financeiro.data <= data_fim,
            entities.Financeiro.caixa_id == caixa.id
        ).all()

        total_vendas = Decimal('0.00')
        for lanc in lancamentos:
            total_vendas += Decimal(str(lanc.valor))

        # --- Total de DESPESAS do dia ---
        despesas = listar_despesas_do_dia(db.session, fuso="America/Sao_Paulo")
        print(f"Despesas do dia: {len(despesas)} registros encontrados\n{despesas}")
        total_despesas = Decimal('0.00')
        for desp in despesas:
            if desp.caixa_id == caixa.id:
                total_despesas += Decimal(str(desp.valor))
                print(f"Despesa encontrada: {desp.descricao} - Valor: {desp.valor}")

        print(f"Total Vendas: {total_vendas}, Total Despesas: {total_despesas}")

        # --- Lógica do saldo: subtrai despesas das vendas (ou da abertura, se não houver venda) ---
        abertura = Decimal(str(caixa.valor_abertura))
        if total_vendas > 0:
            saldo = total_vendas - total_despesas
        else:
            abertura = Decimal(str(caixa.valor_abertura)) - total_despesas
            saldo = 0

        return jsonify({
            'saldo': float(saldo),
            'saldo_formatado': f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_abertura': float(abertura),
            'message': 'Saldo atualizado com sucesso',
            'caixa_id': caixa.id
        })

    except Exception as e:
        app.logger.error(f"Erro ao calcular saldo: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# ===== API ABERTURA DE CAIXA =====
@operador_bp.route('/api/abrir-caixa', methods=['POST'])
@login_required
@operador_required
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
@operador_required
def api_fechar_caixa():
    try:
        data = request.get_json()
        
        # Verificação mais robusta do valor
        if 'valor_fechamento' not in data:
            return jsonify({'error': 'Campo valor_fechamento é obrigatório'}), 400
            
        try:
            valor = Decimal(str(data['valor_fechamento']))
        except (TypeError, ValueError, InvalidOperation):
            return jsonify({'error': 'Valor de fechamento inválido'}), 400
        
        if valor <= 0:
            return jsonify({'error': 'Valor de fechamento deve ser positivo'}), 400
        
        # Restante da função permanece igual
        caixa = fechar_caixa(
            db.session,
            current_user.id,
            valor,
            data.get('observacao', '')
        )
        
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
        app.logger.error(f"Erro na busca de produtos: {str(e)}", exc_info=True)
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
        return jsonify({"erro": "Descrição, valor e caixa_id são obrigatórios"}), 400

    try:
        # Pega o horário atual no fuso America/Sao_Paulo (pode ajustar para Fortaleza ou outro)
        agora = datetime.now(ZoneInfo("America/Sao_Paulo"))

        despesa = entities.Financeiro(
            tipo=entities.TipoMovimentacao.saida,
            categoria=entities.CategoriaFinanceira.despesa,
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

        return jsonify({"mensagem": "Despesa registrada com sucesso"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500
    
@operador_bp.route('/api/produtos/<int:produto_id>/descontos', methods=['GET'])
@login_required
@operador_required
def api_get_produto_descontos(produto_id):
    try:
        # Busca o produto
        produto = db.session.query(entities.Produto).get(produto_id)
        if not produto:
            return jsonify({'error': 'Produto não encontrado'}), 404
        
        # Busca todos os descontos associados a este produto
        descontos = db.session.query(entities.Desconto)\
            .join(entities.produto_desconto_association)\
            .filter(entities.produto_desconto_association.c.produto_id == produto_id)\
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
        app.logger.error(f"Erro ao buscar descontos do produto {produto_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao buscar descontos'}), 500