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
from app.utils.format_data_moeda import format_number
from app.utils.nfce import gerar_nfce_pdf_bobina_bytesio
from app.models.entities import (
     Caixa, Cliente, ContaReceber, Desconto, Entrega, Financeiro, NotaFiscal,
     NotaFiscalItem, PagamentoNotaFiscal, Produto, TipoDesconto, TipoEstoque, 
     TipoUsuario, produto_desconto_association, NotaFiscal
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
        cliente =  Cliente.query.get(cliente_id)
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
                
                produto =  Produto.query.get(produto_id)
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
            
        except (ValueError, InvalidOperation, TypeError) as e:
            app.logger.error(f"Erro ao verificar pagamentos: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Dados de pagamento inválidos'
            }), 400

        # Verificar caixa aberto
        caixa_aberto = get_caixa_aberto(db.session, operador_id=current_user.id)
        
        if not caixa_aberto:
            app.logger.error("Nenhum caixa aberto encontrado")
            return jsonify({
                'success': False,
                'message': 'Nenhum caixa aberto encontrado'
            }), 400

        # Criar registro de Nota Fiscal
        nota =  NotaFiscal(
            cliente_id=cliente.id,
            operador_id=current_user.id,
            caixa_id=caixa_aberto.id,
            data_emissao=datetime.now(),
            valor_total=valor_total,
            valor_desconto=total_descontos,
            tipo_desconto=None,
            status= StatusNota.emitida,
            forma_pagamento= FormaPagamento.dinheiro,  # Será atualizado abaixo
            valor_recebido=valor_recebido,
            troco=max(valor_recebido - valor_total, Decimal(0)) if not a_prazo_usado else Decimal(0),
            a_prazo=a_prazo_usado
        )

        # Criar Entrega, se presente - COM TRATAMENTO SEGURO
        endereco_entrega = dados_venda.get('endereco_entrega')
        if endereco_entrega and isinstance(endereco_entrega, dict):
            entrega =  Entrega(
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
            produto =  Produto.query.get(produto_id)
            quantidade = Decimal(str(item_data.get('quantidade')))
            valor_unitario = Decimal(str(item_data.get('valor_unitario')))
            valor_total_item = Decimal(str(item_data.get('valor_total')))
            desconto_aplicado = Decimal(str(item_data.get('valor_desconto', 0)))
            
            # Tratamento seguro para desconto_info
            desconto_info = item_data.get('desconto_info', {}) or {}
            tipo_desconto = desconto_info.get('tipo') if isinstance(desconto_info, dict) else None

            item_nf =  NotaFiscalItem(
                nota_id=nota.id,
                produto_id=produto_id,
                estoque_origem= TipoEstoque.loja,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total_item,
                desconto_aplicado=desconto_aplicado,
                tipo_desconto= TipoDesconto(tipo_desconto) if tipo_desconto else None,
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
            
            pagamento_nf =  PagamentoNotaFiscal(
                nota_fiscal_id=nota.id,
                forma_pagamento= FormaPagamento(forma),
                valor=valor,
                data=datetime.now(),
                sincronizado=False
            )
            db.session.add(pagamento_nf)
            db.session.flush()  # Garante que teremos o ID do pagamento
            
            pagamentos_ids.append(pagamento_nf.id)
            
            # Registrar no financeiro APENAS se não for a prazo
            if forma != 'a_prazo':
                financeiro =  Financeiro(
                    tipo= TipoMovimentacao.entrada,
                    categoria= CategoriaFinanceira.venda,
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
            conta_receber =  ContaReceber(
                cliente_id=cliente.id,
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo NF #{nota.id}",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=datetime.now() + timedelta(days=30),
                status= StatusPagamento.pendente,
                sincronizado=False
            )
            db.session.add(conta_receber)

        # Atualizar a forma de pagamento principal da nota fiscal
        if len(dados_venda['pagamentos']) == 1:
            # Se houver apenas um pagamento, usa essa forma
            nota.forma_pagamento =  FormaPagamento(dados_venda['pagamentos'][0]['forma_pagamento'])
        else:
            # Se houver múltiplos pagamentos, define como "misto"
            nota.forma_pagamento =  FormaPagamento.dinheiro  # Ou criar um enum para "misto"

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
        # Obtém parâmetros de filtro com validação
        data_str = request.args.get('data')
        operador_id = request.args.get('operador_id', type=int)
        
        # Verificação robusta do caixa
        caixa = get_caixa_aberto(db.session, operador_id=current_user.id)
        if not caixa:
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
                return jsonify({
                    'success': False,
                    'message': 'Formato de data inválido. Use YYYY-MM-DD'
                }), 400

        # Construção da query com prevenção de duplicatas
        inicio_dia = datetime.combine(data_filtro, time.min).replace(tzinfo=tz)
        fim_dia = datetime.combine(data_filtro, time.max).replace(tzinfo=tz)

        # Query principal com distinct para evitar duplicatas no JOIN
        vendas = db.session.query( NotaFiscal).distinct(
             NotaFiscal.id
        ).options(
            db.joinedload( NotaFiscal.cliente),
            db.joinedload( NotaFiscal.operador),
            db.joinedload( NotaFiscal.caixa),
            db.joinedload( NotaFiscal.itens).joinedload( NotaFiscalItem.produto),
            db.joinedload( NotaFiscal.pagamentos)
        ).filter(
             NotaFiscal.caixa_id == caixa.id,
             NotaFiscal.status ==  StatusNota.emitida,
             NotaFiscal.data_emissao >= inicio_dia,
             NotaFiscal.data_emissao <= fim_dia
        )

        # Filtro adicional por operador
        if operador_id and operador_id != current_user.id:
            # Verifica se o usuário tem permissão para consultar outros operadores
            if not current_user.tipo ==  TipoUsuario.admin:
                return jsonify({
                    'success': False,
                    'message': 'Apenas administradores podem filtrar por outros operadores'
                }), 403
            vendas = vendas.filter( NotaFiscal.operador_id == operador_id)
        else:
            vendas = vendas.filter( NotaFiscal.operador_id == current_user.id)

        # Execução da query
        vendas_lista = vendas.order_by( NotaFiscal.data_emissao.desc()).all()

        # Processamento dos resultados com verificação de duplicatas
        ids_vistas = set()
        vendas_unicas = []
        
        for venda in vendas_lista:
            if venda.id in ids_vistas:
                continue
            ids_vistas.add(venda.id)
            vendas_unicas.append(venda)

        # Agregação de pagamentos para evitar duplicação
        def agregar_pagamentos(pagamentos):
            agregados = {}
            for pag in pagamentos:
                chave = (pag.forma_pagamento, pag.data.date())
                if chave in agregados:
                    agregados[chave]['valor'] += float(pag.valor)
                else:
                    agregados[chave] = {
                        'forma_pagamento': pag.forma_pagamento.value,
                        'valor': float(pag.valor),
                        'data': pag.data.isoformat()
                    }
            return list(agregados.values())

        # Formatação final
        resultado = []
        total_geral = Decimal('0.00')
        
        for venda in vendas_unicas:
            total_venda = Decimal(str(venda.valor_total))
            total_geral += total_venda
            
            resultado.append({
                'id': venda.id,
                'data_emissao': venda.data_emissao.astimezone(tz).isoformat(),
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
                'pagamentos': agregar_pagamentos(venda.pagamentos) if venda.pagamentos else []
            })
        print(f'Vendas do dia: \n{resultado}')
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
        app.logger.error(f"Erro em obter_vendas_hoje: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Erro interno ao processar vendas'
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
        
        print(f'Detalhes: \n{detalhes}\n')
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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm
    from io import BytesIO
    from flask import send_file, request, jsonify
    from datetime import datetime
    from sqlalchemy import func

    data_str = request.args.get('data')
    caixa = get_caixa_aberto(db.session, operador_id=current_user.id)
    caixa_id = caixa.id
    operador_id = current_user.id
    data = None

    if data_str:
        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    # Se não especificar data, usar data atual
    data_relatorio = data if data else datetime.now().date()

    # --- Buscar dados das vendas ---
    resultado = obter_detalhes_vendas_dia(data, caixa_id, operador_id)
    if not resultado['success']:
        return jsonify(resultado), 400

    dados = resultado['data']

    # --- Buscar métricas de pagamento por forma de pagamento (do dia atual) ---
    inicio_dia = datetime.combine(data_relatorio, datetime.min.time())
    fim_dia = datetime.combine(data_relatorio, datetime.max.time())

    pagamentos_por_forma = db.session.query(
        PagamentoNotaFiscal.forma_pagamento,
        func.sum(PagamentoNotaFiscal.valor).label('total_valor'),
        func.count(PagamentoNotaFiscal.id).label('total_transacoes')
    ).join(
        NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id
    ).filter(
        NotaFiscal.caixa_id == caixa_id,
        NotaFiscal.operador_id == operador_id,
        NotaFiscal.status == StatusNota.emitida,
        PagamentoNotaFiscal.data >= inicio_dia,
        PagamentoNotaFiscal.data <= fim_dia
    ).group_by(
        PagamentoNotaFiscal.forma_pagamento
    ).all()

    # Converter para dicionário para facilitar o uso
    metricas_pagamento = {
        pagamento.forma_pagamento: {
            'total': float(pagamento.total_valor),
            'transacoes': pagamento.total_transacoes
        }
        for pagamento in pagamentos_por_forma
    }

    # --- Geração do PDF usando platypus ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=40
    )
    elements = []

    # --- Estilos ---
    styles = getSampleStyleSheet()
    normal = styles['Normal']

    left_style = ParagraphStyle(name='Left', parent=normal, alignment=0, fontSize=11)
    center_style = ParagraphStyle(name='Center', parent=normal, alignment=1, fontSize=11)
    bold_center = ParagraphStyle(name='BoldCenter', parent=center_style, fontSize=13, leading=14, spaceAfter=10)
    bold_left = ParagraphStyle(name='BoldLeft', parent=left_style, fontSize=12, leading=14, spaceAfter=8)
    descricao_style = ParagraphStyle(name='DescricaoPequena', fontSize=8, leading=10, wordWrap='CJK')
    wrap_style = ParagraphStyle(name='WrapCell', fontSize=9, leading=11, wordWrap='CJK', alignment=0)
    estorno_style = ParagraphStyle(name='EstornoStyle', parent=bold_left, textColor=colors.red)

    def moeda_br(valor):
        return format_number(valor)

    # --- Título ---
    elements.append(Paragraph(f"RELATÓRIO DIÁRIO DETALHADO DE VENDAS", bold_center))
    elements.append(Spacer(1, 8))

    # --- Informações do Cabeçalho ---
    elements.append(Paragraph(f"Data: {data_relatorio.strftime('%d/%m/%Y')}", left_style))
    elements.append(Paragraph(f"Caixa ID: {caixa_id}", left_style))
    elements.append(Paragraph(f"Operador ID: {operador_id}", left_style))
    elements.append(Paragraph(f"Valor de Abertura: {moeda_br(caixa.valor_abertura)}", left_style))
    
    if caixa.valor_fechamento:
        elements.append(Paragraph(f"Valor de Fechamento: {moeda_br(caixa.valor_fechamento)}", left_style))
    if caixa.valor_confirmado:
        elements.append(Paragraph(f"Valor Confirmado: {moeda_br(caixa.valor_confirmado)}", left_style))
    
    elements.append(Spacer(1, 12))

    # --- Cálculos do Resumo ---
    total_vendas_positivas = sum(v['valor_total'] for v in dados['vendas'] if v['valor_total'] > 0)
    total_estornos = sum(abs(v['valor_total']) for v in dados['vendas'] if v['valor_total'] < 0)
    total_liquido = total_vendas_positivas - total_estornos

    # --- Tabela: Resumo Financeiro ---
    elements.append(Paragraph("RESUMO FINANCEIRO", bold_center))
    
    dados_resumo = [
        ["Descrição", "Valor (R$)"],
        ["Total de Vendas", moeda_br(total_vendas_positivas)],
        ["Total de Estornos", moeda_br(total_estornos)],
        ["Total de Descontos", moeda_br(dados['total_descontos'])],
        ["Total de Entradas", moeda_br(dados['total_entradas'])],
        ["Total de Saídas", moeda_br(dados['total_saidas'])],
        ["Saldo Líquido", moeda_br(total_liquido)]
    ]

    tabela_resumo = Table(dados_resumo, colWidths=[220, 140], hAlign='CENTER')
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.red),  # Estornos em vermelho
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),  # Saldo líquido em negrito
    ]))
    elements.append(tabela_resumo)
    elements.append(Spacer(1, 16))

    # --- NOVA SEÇÃO: Métricas de Pagamento por Forma ---
    elements.append(Paragraph("PAGAMENTOS POR FORMA DE PAGAMENTO", bold_center))
    
    # Preparar dados da tabela de pagamentos
    dados_pagamentos = [["Forma de Pagamento", "Qtd Transações", "Total (R$)"]]
    
    total_geral_pagamentos = 0
    total_geral_transacoes = 0
    
    # Ordenar por valor total (decrescente)
    formas_ordenadas = sorted(metricas_pagamento.items(), 
                             key=lambda x: x[1]['total'], 
                             reverse=True)
    
    for forma, dados_forma in formas_ordenadas:
        # Converter enum para string mais legível
        forma_nome = forma.value if hasattr(forma, 'value') else str(forma)
        forma_nome = forma_nome.replace('_', ' ').title()
        
        dados_pagamentos.append([
            forma_nome,
            str(dados_forma['transacoes']),
            moeda_br(dados_forma['total'])
        ])
        
        total_geral_pagamentos += dados_forma['total']
        total_geral_transacoes += dados_forma['transacoes']
    
    # Adicionar linha de total
    dados_pagamentos.append([
        "TOTAL GERAL",
        str(total_geral_transacoes),
        moeda_br(total_geral_pagamentos)
    ])

    tabela_pagamentos = Table(dados_pagamentos, colWidths=[180, 90, 90], hAlign='CENTER')
    tabela_pagamentos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),  # Linha de total
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Linha de total em negrito
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    elements.append(tabela_pagamentos)
    elements.append(Spacer(1, 16))

    # --- Detalhes das Vendas ---
    elements.append(Paragraph("DETALHES DAS VENDAS", bold_center))
    elements.append(Spacer(1, 8))

    for i, venda in enumerate(dados['vendas']):
        is_estorno = venda['valor_total'] < 0
        valor_exibicao = abs(venda['valor_total'])

        # Título da venda
        if is_estorno:
            titulo_venda = f"ESTORNO DA VENDA #{venda['id']}"
            elements.append(Paragraph(titulo_venda, estorno_style))
        else:
            titulo_venda = f"VENDA #{venda['id']}"
            elements.append(Paragraph(titulo_venda, bold_left))

        # Informações da venda
        info_venda_data = [
            ["Cliente:", venda['cliente']],
            ["Data/Hora:", datetime.fromisoformat(venda['data']).strftime('%d/%m/%Y %H:%M')],
            ["Operador:", venda['operador']],
            ["Valor Total:", moeda_br(valor_exibicao)],
            ["Desconto:", moeda_br(venda['valor_desconto'])],
            ["Forma Pagamento:", venda['forma_pagamento']],
            ["A Prazo:", "Sim" if venda['a_prazo'] else "Não"],
            ["Tipo:", "ESTORNO" if is_estorno else "VENDA NORMAL"]
        ]

        tabela_info_venda = Table(info_venda_data, colWidths=[100, 200], hAlign='LEFT')
        estilo_info_venda = [
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]
        
        if is_estorno:
            estilo_info_venda.append(('TEXTCOLOR', (0, 7), (1, 7), colors.red))
            estilo_info_venda.append(('FONTNAME', (0, 7), (1, 7), 'Helvetica-Bold'))

        tabela_info_venda.setStyle(TableStyle(estilo_info_venda))
        elements.append(tabela_info_venda)
        elements.append(Spacer(1, 8))

        # Itens da venda
        elements.append(Paragraph("ITENS:", ParagraphStyle(name='ItemsTitle', parent=left_style, fontSize=10, leading=12)))
        
        dados_itens = [["Produto", "Qtd", "V. Unit.", "V. Total", "Desconto"]]
        
        for item in venda['itens']:
            quantidade = -item['quantidade'] if is_estorno else item['quantidade']
            valor_total_item = -item['valor_total'] if is_estorno else item['valor_total']
            desconto_item = -item['desconto'] if is_estorno and item['desconto'] else item['desconto']
            
            produto_paragraph = Paragraph(item['produto'], wrap_style)
            
            dados_itens.append([
                produto_paragraph,
                f"{quantidade:.3f}",
                moeda_br(item['valor_unitario']),
                moeda_br(valor_total_item),
                moeda_br(desconto_item) if desconto_item > 0 else "-"
            ])

        tabela_itens = Table(dados_itens, colWidths=[180, 50, 70, 70, 60], hAlign='CENTER')
        estilo_itens = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]
        
        if is_estorno:
            estilo_itens.append(('TEXTCOLOR', (0, 1), (-1, -1), colors.red))

        tabela_itens.setStyle(TableStyle(estilo_itens))
        elements.append(tabela_itens)
        
        # Espaçamento entre vendas (exceto na última)
        if i < len(dados['vendas']) - 1:
            elements.append(Spacer(1, 16))

    # --- Área para assinaturas ---
    elements.append(Spacer(1, 30))
    
    # Criar linhas de assinatura simples
    assinatura_data = [
        ["_" * 40, "_" * 40],
        ["Assinatura do Operador", "Assinatura do Administrador"]
    ]
    
    tabela_assinaturas = Table(assinatura_data, colWidths=[270, 270], hAlign='CENTER')
    tabela_assinaturas.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
    ]))
    elements.append(tabela_assinaturas)

    # --- Build do documento ---
    doc.build(elements)
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
        # Busca apenas o caixa do operador logado
        caixa = get_caixa_aberto(db.session, operador_id=current_user.id)

        if not caixa:
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
        lancamentos = db.session.query( Financeiro).join(
             NotaFiscal,
             Financeiro.nota_fiscal_id ==  NotaFiscal.id,
            isouter=True
        ).filter(
             Financeiro.tipo ==  TipoMovimentacao.entrada,
             Financeiro.categoria ==  CategoriaFinanceira.venda,
             Financeiro.data >= data_inicio,
             Financeiro.data <= data_fim,
             Financeiro.caixa_id == caixa.id,
            # Filtro para notas fiscais: ou é nula (não tem nota) ou não está cancelada
            db.or_(
                 NotaFiscal.id.is_(None),
                 NotaFiscal.status !=  StatusNota.cancelada
            )
        ).all()

        total_vendas = Decimal('0.00')
        for lanc in lancamentos:
            print(lanc.valor)
            total_vendas += Decimal(str(lanc.valor))

        # --- Total de DESPESAS do dia ---
        # Busca despesas apenas do caixa do operador atual
        despesas = db.session.query( Financeiro).filter(
             Financeiro.tipo ==  TipoMovimentacao.saida,
             Financeiro.categoria ==  CategoriaFinanceira.despesa,
             Financeiro.data >= data_inicio,
             Financeiro.data <= data_fim,
             Financeiro.caixa_id == caixa.id
        ).all()

        print(f"Despesas do caixa {caixa.id}: {len(despesas)} registros encontrados")
        
        total_despesas = Decimal('0.00')
        for desp in despesas:
            total_despesas += Decimal(str(desp.valor))
            print(f"Despesa encontrada: {desp.descricao} - Valor: {desp.valor}")

        print(f"Caixa ID: {caixa.id} | Operador: {current_user.nome}")
        print(f"Total Vendas: {total_vendas}, Total Despesas: {total_despesas}")

        # --- Lógica do saldo: abertura + vendas - despesas ---
        abertura = Decimal(str(caixa.valor_abertura))
        saldo = total_vendas - total_despesas

        return jsonify({
            'saldo': float(saldo),
            'saldo_formatado': f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_abertura': float(abertura),
            'total_vendas': float(total_vendas),
            'total_despesas': float(total_despesas),
            'message': 'Saldo atualizado com sucesso',
            'caixa_id': caixa.id,
            'operador_nome': current_user.nome
        })

    except Exception as e:
        app.logger.error(f"Erro ao calcular saldo para operador {current_user.id}: {str(e)}")
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
        produto = db.session.query( Produto).get(produto_id)
        if not produto:
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
        app.logger.error(f"Erro ao buscar descontos do produto {produto_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno ao buscar descontos'}), 500