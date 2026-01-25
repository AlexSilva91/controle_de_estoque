import csv
from functools import wraps
import io
import locale
import math
from math import ceil
from weasyprint import HTML
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import os
from zoneinfo import ZoneInfo
from flask import (
    Blueprint,
    Response,
    abort,
    app,
    current_app,
    render_template,
    request,
    jsonify,
)
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload
import traceback
from flask import send_file, make_response, jsonify
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Table as PlatypusTable,
)
from sqlalchemy import Date, cast, extract
from flask import make_response, request, jsonify
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
from datetime import datetime, date, time
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from app.models import db
from app.utils.audit import calcular_diferencas
from app.utils.format_data_moeda import (
    format_currency,
    format_number,
    formatar_data_br2,
    formatarMoeda,
    to_decimal_or_none,
)
from app.models.entities import (
    AuditLog,
    Cliente,
    Configuracao,
    Conta,
    LoteEstoque,
    MovimentacaoConta,
    NFeXML,
    Produto,
    NotaFiscal,
    SaldoFormaPagamento,
    TipoUsuario,
    UnidadeMedida,
    StatusNota,
    Financeiro,
    TipoMovimentacao,
    CategoriaFinanceira,
    MovimentacaoEstoque,
    ContaReceber,
    StatusPagamento,
    Caixa,
    StatusCaixa,
    NotaFiscalItem,
    FormaPagamento,
    Entrega,
    TipoDesconto,
    PagamentoNotaFiscal,
    Desconto,
    PagamentoContaReceber,
    Usuario,
    produto_desconto_association,
)
from app.crud import (
    TipoEstoque,
    arredondar_preco_venda,
    atualizar_desconto,
    atualizar_estoque_produto,
    atualizar_venda,
    buscar_desconto_by_id,
    buscar_descontos_por_produto_id,
    buscar_historico_financeiro,
    buscar_historico_financeiro_agrupado,
    buscar_produtos_por_unidade,
    buscar_todos_os_descontos,
    calcular_fator_conversao,
    calcular_formas_pagamento,
    criar_desconto,
    deletar_desconto,
    determinar_unidade_produto,
    estornar_venda,
    extrair_chave_acesso,
    extrair_dados_nfe_completo,
    extrair_marca_produto,
    get_caixa_aberto,
    abrir_caixa,
    fechar_caixa,
    get_caixas,
    get_caixa_by_id,
    TipoEstoque,
    atualizar_desconto,
    buscar_desconto_by_id,
    buscar_descontos_por_produto_id,
    buscar_historico_financeiro,
    buscar_historico_financeiro_agrupado,
    buscar_produtos_por_unidade,
    buscar_todos_os_descontos,
    calcular_fator_conversao,
    criar_desconto,
    criar_ou_atualizar_lote,
    deletar_desconto,
    estornar_venda,
    get_caixa_aberto,
    abrir_caixa,
    fechar_caixa,
    get_caixas,
    get_caixa_by_id,
    get_caixas_fechado,
    get_caixas_fechado,
    get_transferencias,
    get_user_by_id,
    get_usuarios,
    create_user,
    get_venda_completa,
    obter_caixas_completo,
    salvar_nfe_xml_completo,
    to_decimal,
    transferir_produto,
    transferir_todo_saldo,
    update_user,
    get_produto,
    get_produtos,
    create_produto,
    update_produto,
    delete_produto,
    registrar_movimentacao,
    get_cliente,
    create_cliente,
    update_cliente,
    delete_cliente,
    create_nota_fiscal,
    get_nota_fiscal,
    get_notas_fiscais,
    create_lancamento_financeiro,
    get_lancamentos_financeiros,
    update_lancamento_financeiro,
    delete_lancamento_financeiro,
    get_clientes_all,
    get_caixas_abertos,
    processar_movimentacoes_conta,
)
from app.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    ProdutoCreate,
    ProdutoUpdate,
    MovimentacaoEstoqueCreate,
    ClienteCreate,
    ClienteUpdate,
    FinanceiroCreate,
    FinanceiroUpdate,
)
import logging
from app.utils.format_data_moeda import formatar_data_br, format_number
from app.utils.nfce import generate_caixa_financeiro_pdf
from app.utils.signature import SignatureLine
from app.utils.upload import (
    get_product_photo_url,
    save_product_photo,
    delete_product_photo,
)

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "message": "Acesso não autorizado"}), 401
        if (
            current_user.tipo != "admin"
        ):  # Supondo que 'tipo' seja o campo que define o tipo de usuário
            return (
                jsonify(
                    {"success": False, "message": "Acesso restrito a administradores"}
                ),
                403,
            )
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
        decimal_value = Decimal(str_value).quantize(Decimal("0.01"))
        return decimal_value
    except (InvalidOperation, ValueError):
        return None


# ===== Dashboard Routes =====
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    logger.info(f"Acessando dashboard admin - Usuário: {current_user.nome}")
    return render_template("dashboard_admin.html", nome_usuario=current_user.nome)


@admin_bp.route("/dashboard/metrics")
@login_required
@admin_required
def get_dashboard_metrics():
    try:
        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1).date()

        estoque_metrics = (
            db.session.query(
                Produto.unidade, func.sum(Produto.estoque_loja).label("total")
            )
            .filter(Produto.ativo == True)
            .group_by(Produto.unidade)
            .all()
        )

        estoque_dict = {"kg": 0, "saco": 0, "unidade": 0}

        for item in estoque_metrics:
            if item.unidade == UnidadeMedida.kg:
                estoque_dict["kg"] = item.total or 0
            elif item.unidade == UnidadeMedida.saco:
                estoque_dict["saco"] = item.total or 0
            elif item.unidade == UnidadeMedida.unidade:
                estoque_dict["unidade"] = item.total or 0

        inicio_mes = datetime.combine(primeiro_dia_mes, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())

        vendas_mes = (
            db.session.query(func.sum(PagamentoNotaFiscal.valor))
            .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
            .join(Caixa, NotaFiscal.caixa_id == Caixa.id)
            .filter(
                NotaFiscal.status == StatusNota.emitida,
                Caixa.data_abertura >= inicio_mes,
                Caixa.data_abertura <= fim_dia,
            )
            .scalar()
            or 0
        )

        contas_recebidas_mes = (
            db.session.query(func.sum(PagamentoContaReceber.valor_pago))
            .join(Caixa, PagamentoContaReceber.caixa_id == Caixa.id)
            .filter(Caixa.data_abertura >= inicio_mes, Caixa.data_abertura <= fim_dia)
            .scalar()
            or 0
        )

        # 3. Estornos (saida_estorno) para deduzir
        estornos_mes = (
            db.session.query(func.sum(Financeiro.valor))
            .join(Caixa, Financeiro.caixa_id == Caixa.id)
            .filter(
                Financeiro.tipo == TipoMovimentacao.saida_estorno,
                Caixa.data_abertura >= inicio_mes,
                Caixa.data_abertura <= fim_dia,
            )
            .scalar()
            or 0
        )

        entradas_brutas_mes = float(vendas_mes) + float(contas_recebidas_mes)
        entradas_liquidas_mes = entradas_brutas_mes - float(estornos_mes)

        saidas_mes = (
            db.session.query(func.sum(Financeiro.valor))
            .join(Caixa, Financeiro.caixa_id == Caixa.id)
            .filter(
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria == CategoriaFinanceira.despesa,
                Caixa.data_abertura >= inicio_mes,
                Caixa.data_abertura <= fim_dia,
            )
            .scalar()
            or 0
        )

        saldo_mes = entradas_liquidas_mes - float(saidas_mes)

        return jsonify(
            {
                "success": True,
                "metrics": {
                    "estoque": {
                        "kg": f"{format_number(estoque_dict['kg'], is_weight=True)} kg",
                        "sacos": f"{format_number(estoque_dict['saco'], is_weight=True)} sacos",
                        "unidades": f"{format_number(estoque_dict['unidade'], is_weight=True)} un",
                    },
                    "financeiro": {
                        "entradas_mes": format_currency(entradas_liquidas_mes),
                        "saidas_mes": format_currency(saidas_mes),
                        "saldo_mes": format_currency(saldo_mes),
                    },
                },
            }
        )

    except Exception as e:
        logger.error(f"Erro na consulta de métricas: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/dashboard/vendas-diarias")
@login_required
@admin_required
def get_vendas_diarias():
    try:
        data_inicio_str = request.args.get("data_inicio")
        data_fim_str = request.args.get("data_fim")
        todos = request.args.get("todos") == "true"

        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()

        if data_inicio_str and data_fim_str and not todos:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()

            if data_fim > hoje:
                data_fim = hoje
        else:
            data_inicio = hoje - timedelta(days=6)
            data_fim = hoje

        dados_diarios = []

        if data_inicio_str and data_fim_str and not todos:
            periodo_caixa_inicio = data_inicio
            periodo_caixa_fim = data_fim
        else:
            periodo_caixa_inicio = hoje - timedelta(days=30)
            periodo_caixa_fim = hoje

        vendas_periodo = (
            db.session.query(
                Caixa.id.label("caixa_id"),
                Caixa.data_abertura,
                func.sum(Financeiro.valor).label("total_vendas"),
            )
            .join(Financeiro, Financeiro.caixa_id == Caixa.id)
            .filter(
                Financeiro.tipo == TipoMovimentacao.entrada,
                Financeiro.categoria == CategoriaFinanceira.venda,
                Financeiro.data >= periodo_caixa_inicio,
                Financeiro.data <= periodo_caixa_fim,
            )
            .group_by(Caixa.id, Caixa.data_abertura)
            .order_by(Caixa.data_abertura.asc())
            .all()
        )

        current_date = data_inicio

        while current_date <= data_fim:
            total_vendas = (
                db.session.query(func.sum(Financeiro.valor))
                .filter(
                    Financeiro.tipo == TipoMovimentacao.entrada,
                    Financeiro.categoria == CategoriaFinanceira.venda,
                    func.date(Financeiro.data) == current_date,
                )
                .scalar()
                or 0
            )

            total_despesas = (
                db.session.query(func.sum(Financeiro.valor))
                .filter(
                    Financeiro.tipo == TipoMovimentacao.saida,
                    Financeiro.categoria == CategoriaFinanceira.despesa,
                    func.date(Financeiro.data) == current_date,
                )
                .scalar()
                or 0
            )

            formas_pagamento = (
                db.session.query(
                    PagamentoNotaFiscal.forma_pagamento,
                    func.sum(PagamentoNotaFiscal.valor).label("total"),
                )
                .join(NotaFiscal, NotaFiscal.id == PagamentoNotaFiscal.nota_fiscal_id)
                .filter(
                    func.date(NotaFiscal.data_emissao) == current_date,
                    NotaFiscal.status == StatusNota.emitida,
                )
                .group_by(PagamentoNotaFiscal.forma_pagamento)
                .all()
            )

            dados_diarios.append(
                {
                    "data": current_date.strftime("%d/%m"),
                    "total_vendas": format_currency(total_vendas),
                    "total_despesas": format_currency(total_despesas),
                    "saldo_dia": format_currency(total_vendas - total_despesas),
                    "formas_pagamento": [
                        {
                            "forma": fp.forma_pagamento.value,
                            "total": format_currency(fp.total or 0),
                        }
                        for fp in formas_pagamento
                    ],
                }
            )

            current_date += timedelta(days=1)

        total_vendas_periodo = (
            db.session.query(func.sum(Financeiro.valor))
            .filter(
                Financeiro.tipo == TipoMovimentacao.entrada,
                Financeiro.categoria == CategoriaFinanceira.venda,
                Financeiro.data >= data_inicio,
                Financeiro.data <= data_fim,
            )
            .scalar()
            or 0
        )

        total_despesas_periodo = (
            db.session.query(func.sum(Financeiro.valor))
            .filter(
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria == CategoriaFinanceira.despesa,
                Financeiro.data >= data_inicio,
                Financeiro.data <= data_fim,
            )
            .scalar()
            or 0
        )

        return jsonify(
            {
                "success": True,
                "dados": dados_diarios,
                "vendas_mensais_caixa": [
                    {
                        "data_abertura": caixa.data_abertura.strftime("%d/%m/%Y"),
                        "total_vendas": format_currency(caixa.total_vendas or 0),
                    }
                    for caixa in vendas_periodo
                ],
                "resumo_mensal": {
                    "total_vendas": format_currency(total_vendas_periodo),
                    "total_despesas": format_currency(total_despesas_periodo),
                    "saldo_mensal": format_currency(
                        total_vendas_periodo - total_despesas_periodo
                    ),
                },
                "periodo": {
                    "inicio": data_inicio.strftime("%d/%m/%Y"),
                    "fim": data_fim.strftime("%d/%m/%Y"),
                },
                "com_filtro": bool(data_inicio_str and data_fim_str and not todos),
            }
        )
    except Exception as e:
        logger.error(f"Erro na consulta de vendas diárias: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/dashboard/vendas-mensais")
@login_required
@admin_required
def get_vendas_mensais():
    try:
        data_inicio_str = request.args.get("data_inicio")
        data_fim_str = request.args.get("data_fim")

        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        meses = []
        vendas = []
        despesas = []

        if data_inicio_str and data_fim_str:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
            meses_intervalo = []
            atual = data_inicio

            while atual <= data_fim:
                meses_intervalo.append((atual.year, atual.month))
                # Avança um mês
                if atual.month == 12:
                    atual = atual.replace(year=atual.year + 1, month=1)
                else:
                    atual = atual.replace(month=atual.month + 1)
        else:
            # Últimos 6 meses
            meses_intervalo = []
            for i in range(5, -1, -1):
                mes = hoje.month - i
                ano = hoje.year
                if mes <= 0:
                    mes += 12
                    ano -= 1
                meses_intervalo.append((ano, mes))

        for ano, mes in meses_intervalo:
            primeiro_dia = datetime(ano, mes, 1)
            ultimo_dia = (
                datetime(ano, mes + 1, 1) - timedelta(days=1)
                if mes < 12
                else datetime(ano, 12, 31)
            )
            ultimo_dia = ultimo_dia.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            vendas_mes = (
                db.session.query(func.sum(PagamentoNotaFiscal.valor))
                .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
                .join(Caixa, NotaFiscal.caixa_id == Caixa.id)
                .filter(
                    NotaFiscal.status == StatusNota.emitida,
                    Caixa.data_abertura >= primeiro_dia,
                    Caixa.data_abertura <= ultimo_dia,
                )
                .scalar()
                or 0
            )

            contas_recebidas_mes = (
                db.session.query(func.sum(PagamentoContaReceber.valor_pago))
                .join(Caixa, PagamentoContaReceber.caixa_id == Caixa.id)
                .filter(
                    Caixa.data_abertura >= primeiro_dia,
                    Caixa.data_abertura <= ultimo_dia,
                )
                .scalar()
                or 0
            )

            estornos_mes = (
                db.session.query(func.sum(Financeiro.valor))
                .join(Caixa, Financeiro.caixa_id == Caixa.id)
                .filter(
                    Financeiro.tipo == TipoMovimentacao.saida_estorno,
                    Caixa.data_abertura >= primeiro_dia,
                    Caixa.data_abertura <= ultimo_dia,
                )
                .scalar()
                or 0
            )

            entradas_liquidas_mes = (
                float(vendas_mes) + float(contas_recebidas_mes)
            ) - float(estornos_mes)

            saidas_mes = (
                db.session.query(func.sum(Financeiro.valor))
                .join(Caixa, Financeiro.caixa_id == Caixa.id)
                .filter(
                    Financeiro.tipo == TipoMovimentacao.saida,
                    Financeiro.categoria == CategoriaFinanceira.despesa,
                    Caixa.data_abertura >= primeiro_dia,
                    Caixa.data_abertura <= ultimo_dia,
                )
                .scalar()
                or 0
            )

            meses.append(f"{primeiro_dia.strftime('%m/%Y')}")
            vendas.append(entradas_liquidas_mes)
            despesas.append(float(saidas_mes))

        return jsonify(
            {"success": True, "meses": meses, "vendas": vendas, "despesas": despesas}
        )
    except Exception as e:
        logger.error(f"Erro na consulta de vendas mensais: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/dashboard/movimentacoes")
@login_required
@admin_required
def get_movimentacoes():
    try:
        movimentacoes = (
            db.session.query(MovimentacaoEstoque)
            .order_by(MovimentacaoEstoque.data.desc())
            .limit(10)
            .all()
        )

        result = []
        for mov in movimentacoes:
            result.append(
                {
                    "data": mov.data.strftime("%d/%m/%Y"),
                    "tipo": mov.tipo.value.capitalize(),
                    "produto": mov.produto.nome,
                    "quantidade": f"{mov.quantidade:,.2f} {mov.produto.unidade.value}",
                    "valor": f"R$ {mov.valor_unitario * mov.quantidade:,.2f}",
                }
            )

        return jsonify({"success": True, "movimentacoes": result})
    except Exception as e:
        logger.error(f"Erro na consulta de movimentações: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/dashboard/produtos-maior-fluxo")
@login_required
@admin_required
def produtos_maior_fluxo():
    try:
        # Obter filtros de data
        data_inicio_str = request.args.get("data_inicio")
        data_fim_str = request.args.get("data_fim")
        todos = request.args.get("todos") == "true"

        if data_inicio_str and data_fim_str and not todos:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
            # Garantir que data_fim inclua todo o dia
            data_fim = data_fim.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        else:
            # Comportamento padrão: últimos 30 dias
            data_inicio = datetime.now() - timedelta(days=30)
            data_fim = datetime.now()

        # Consulta para obter os produtos com maior saída no período
        produtos_fluxo = (
            db.session.query(
                Produto.nome,
                Produto.valor_unitario_compra,
                func.sum(NotaFiscalItem.quantidade).label("total_saida"),
                func.sum(
                    NotaFiscalItem.quantidade * NotaFiscalItem.valor_unitario
                ).label("valor_total_venda"),
                func.sum(
                    NotaFiscalItem.quantidade * Produto.valor_unitario_compra
                ).label("valor_total_compra"),
            )
            .join(NotaFiscalItem, NotaFiscalItem.produto_id == Produto.id)
            .join(NotaFiscal, NotaFiscal.id == NotaFiscalItem.nota_id)
            .filter(
                NotaFiscal.status == StatusNota.emitida,
                NotaFiscal.data_emissao >= data_inicio,
                NotaFiscal.data_emissao <= data_fim,
            )
            .group_by(Produto.id, Produto.nome, Produto.valor_unitario_compra)
            .order_by(func.sum(NotaFiscalItem.quantidade).desc())
            .limit(10)
            .all()
        )

        # Preparar dados para o gráfico
        produtos = []
        quantidades = []
        valores_venda = []
        valores_compra = []

        for produto in produtos_fluxo:
            produtos.append(produto.nome)
            quantidades.append(float(produto.total_saida))
            valores_venda.append(float(produto.valor_total_venda))
            valor_compra = float(produto.valor_total_compra or 0)
            valores_compra.append(valor_compra)

        return jsonify(
            {
                "success": True,
                "produtos": produtos,
                "quantidades": quantidades,
                "valores_venda": valores_venda,
                "valores_compra": valores_compra,
                "periodo": {
                    "inicio": data_inicio.strftime("%d/%m/%Y"),
                    "fim": data_fim.strftime("%d/%m/%Y"),
                },
            }
        )

    except Exception as e:
        logger.error(f"Erro ao buscar dados dos produtos: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify(
            {"success": False, "message": "Erro ao buscar dados dos produtos"}
        )


# ===== Caixa Routes =====
@admin_bp.route("/caixa/abrir", methods=["POST"])
@login_required
@admin_required
def abrir_caixa_route():
    try:
        data = request.get_json()
        valor_abertura = Decimal(data.get("valor_abertura"))
        observacao = data.get("observacao", "")

        caixa = abrir_caixa(
            db.session,
            operador_id=current_user.id,
            valor_abertura=valor_abertura,
            observacao=observacao,
        )
        logger.info(f"Caixa {caixa.id} aberto por usuário {current_user.nome}")
        return jsonify(
            {
                "success": True,
                "message": "Caixa aberto com sucesso",
                "caixa": {
                    "id": caixa.id,
                    "data_abertura": caixa.data_abertura.strftime("%d/%m/%Y %H:%M"),
                    "valor_abertura": str(caixa.valor_abertura),
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao abrir caixa: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/caixa/fechar", methods=["POST"])
@login_required
@admin_required
def fechar_caixa_route():
    try:
        data = request.get_json()
        valor_fechamento = Decimal(data.get("valor_fechamento"))
        observacao = data.get("observacao", "")

        caixa = fechar_caixa(
            db.session,
            operador_id=current_user.id,
            valor_fechamento=valor_fechamento,
            observacao=observacao,
        )
        logger.info(f"Caixa {caixa.id} fechado por usuário {current_user.nome}")
        return jsonify(
            {
                "success": True,
                "message": "Caixa fechado com sucesso",
                "caixa": {
                    "id": caixa.id,
                    "data_fechamento": caixa.data_fechamento.strftime("%d/%m/%Y %H:%M"),
                    "valor_fechamento": str(caixa.valor_fechamento),
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao fechar caixa: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/caixa/status")
@login_required
@admin_required
def get_caixa_status():
    try:
        caixa = get_caixas_abertos(db.session)
        if caixa:
            logger.info(
                f"Status do caixa {caixa.id} obtido por usuário {current_user.nome}"
            )
            return jsonify(
                {
                    "success": True,
                    "aberto": True,
                    "caixa": {
                        "id": caixa.id,
                        "data_abertura": caixa.data_abertura.strftime("%d/%m/%Y %H:%M"),
                        "valor_abertura": str(caixa.valor_abertura),
                        "operador": caixa.operador.nome,
                    },
                }
            )
        else:
            return jsonify({"success": True, "aberto": False})
    except Exception as e:
        logger.error(f"Erro ao obter status do caixa: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/caixa/historico")
@login_required
@admin_required
def get_caixa_historico():
    try:
        caixas = get_caixas(db.session)
        result = []
        for caixa in caixas:
            result.append(
                {
                    "id": caixa.id,
                    "data_abertura": caixa.data_abertura.strftime("%d/%m/%Y %H:%M"),
                    "data_fechamento": (
                        caixa.data_fechamento.strftime("%d/%m/%Y %H:%M")
                        if caixa.data_fechamento
                        else None
                    ),
                    "valor_abertura": str(caixa.valor_abertura),
                    "valor_fechamento": (
                        str(caixa.valor_fechamento) if caixa.valor_fechamento else None
                    ),
                    "status": caixa.status.value,
                    "operador": caixa.operador.nome,
                }
            )
        return jsonify({"success": True, "caixas": result})
    except Exception as e:
        logger.error(f"Erro ao obter histórico de caixas: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===== Cliente Routes =====
@admin_bp.route("/clientes", methods=["GET"])
@login_required
@admin_required
def listar_clientes():
    try:
        search = request.args.get("search", "").lower()
        clientes = get_clientes_all(db.session)

        result = []
        for cliente in clientes:
            if search and (
                search not in cliente.nome.lower()
                and search not in (cliente.documento or "").lower()
            ):
                continue

            result.append(
                {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "documento": cliente.documento or "",
                    "telefone": cliente.telefone or "",
                    "email": cliente.email or "",
                    "ativo": "Ativo" if cliente.ativo else "Inativo",
                    "endereco": cliente.endereco or "",
                }
            )

        return jsonify({"success": True, "clientes": result})
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/clientes/<int:cliente_id>/detalhes", methods=["GET"])
@login_required
@admin_required
def obter_detalhes_cliente(cliente_id):
    try:
        cliente = get_cliente(db.session, cliente_id)
        if not cliente:
            return jsonify({"success": False, "message": "Cliente não encontrado"}), 404

        notas_fiscais = NotaFiscal.query.filter_by(cliente_id=cliente_id).all()

        produtos_comprados = []
        produtos_quantidade = {}

        for nota in notas_fiscais:
            for item in nota.itens:
                valor_unit = float(item.valor_unitario)
                valor_total = float(item.valor_total)

                produtos_comprados.append(
                    {
                        "id": item.produto.id,
                        "nome": item.produto.nome,
                        "quantidade": float(item.quantidade),
                        "quantidade_formatada": format_number(item.quantidade),
                        "valor_unitario": valor_unit,
                        "valor_unitario_formatado": format_currency(valor_unit),
                        "valor_total": valor_total,
                        "valor_total_formatado": format_currency(valor_total),
                        "data_compra": nota.data_emissao.isoformat(),
                        "data_compra_br": formatar_data_br(nota.data_emissao),
                        "unidade": (
                            item.produto.unidade.value if item.produto.unidade else "un"
                        ),
                    }
                )

                if item.produto.id in produtos_quantidade:
                    produtos_quantidade[item.produto.id]["quantidade_total"] += float(
                        item.quantidade
                    )
                    produtos_quantidade[item.produto.id]["vezes_comprado"] += 1
                else:
                    produtos_quantidade[item.produto.id] = {
                        "id": item.produto.id,
                        "nome": item.produto.nome,
                        "quantidade_total": float(item.quantidade),
                        "quantidade_total_formatada": format_number(item.quantidade),
                        "vezes_comprado": 1,
                        "unidade": (
                            item.produto.unidade.value if item.produto.unidade else "un"
                        ),
                    }

        produtos_mais_comprados = sorted(
            produtos_quantidade.values(),
            key=lambda x: x["quantidade_total"],
            reverse=True,
        )[:10]

        contas_receber = ContaReceber.query.filter_by(cliente_id=cliente_id).all()

        contas_abertas = []
        contas_quitadas = []

        for conta in contas_receber:
            valor_original = float(conta.valor_original)
            valor_aberto = float(conta.valor_aberto)

            info = {
                "id": conta.id,
                "descricao": conta.descricao,
                "valor_original": valor_original,
                "valor_original_formatado": format_currency(valor_original),
                "valor_aberto": valor_aberto,
                "valor_aberto_formatado": format_currency(valor_aberto),
                "data_vencimento": conta.data_vencimento.isoformat(),
                "data_vencimento_br": formatar_data_br(conta.data_vencimento),
                "data_emissao": conta.data_emissao.isoformat(),
                "data_emissao_br": formatar_data_br(conta.data_emissao),
                "status": conta.status.value,
            }

            if conta.status == StatusPagamento.quitado:
                contas_quitadas.append(info)
            else:
                contas_abertas.append(info)

        valor_total_compras = sum(float(nota.valor_total) for nota in notas_fiscais)
        valor_total_divida = sum(float(c.valor_original) for c in contas_receber)
        valor_total_aberto = sum(float(c.valor_aberto) for c in contas_receber)
        valor_total_pago = (
            valor_total_divida - valor_total_aberto if valor_total_divida > 0 else 0
        )

        porcentagem_pago = (
            (valor_total_pago / valor_total_divida * 100)
            if valor_total_divida > 0
            else 0
        )
        porcentagem_aberto = (
            (valor_total_aberto / valor_total_divida * 100)
            if valor_total_divida > 0
            else 0
        )

        return jsonify(
            {
                "success": True,
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "documento": cliente.documento,
                    "telefone": cliente.telefone,
                    "email": cliente.email,
                    "endereco": cliente.endereco,
                    "limite_credito": float(cliente.limite_credito),
                    "limite_credito_formatado": format_currency(cliente.limite_credito),
                    "ativo": cliente.ativo,
                },
                "produtos_comprados": produtos_comprados,
                "produtos_mais_comprados": produtos_mais_comprados,
                "contas_abertas": contas_abertas,
                "contas_quitadas": contas_quitadas,
                "total_compras": len(notas_fiscais),
                "valor_total_compras": valor_total_compras,
                "valor_total_compras_formatado": format_currency(valor_total_compras),
                "dividas": {
                    "valor_total_divida": valor_total_divida,
                    "valor_total_divida_formatado": format_currency(valor_total_divida),
                    "valor_total_aberto": valor_total_aberto,
                    "valor_total_aberto_formatado": format_currency(valor_total_aberto),
                    "valor_total_pago": valor_total_pago,
                    "valor_total_pago_formatado": format_currency(valor_total_pago),
                    "porcentagem_pago": porcentagem_pago,
                    "porcentagem_aberto": porcentagem_aberto,
                },
            }
        )

    except Exception as e:
        logger.error(f"Erro ao obter detalhes do cliente: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/cliente/contas/<int:conta_id>/detalhes", methods=["GET"])
@login_required
@admin_required
def obter_detalhes_conta(conta_id):
    try:
        conta = ContaReceber.query.get(conta_id)
        if not conta:
            return jsonify({"success": False, "message": "Conta não encontrada"}), 404

        # Dados básicos da conta
        conta_info = {
            "id": conta.id,
            "cliente_id": conta.cliente_id,
            "cliente_nome": conta.cliente.nome if conta.cliente else "N/A",
            "descricao": conta.descricao,
            "valor_original": float(conta.valor_original),
            "valor_original_formatado": format_currency(conta.valor_original),
            "valor_aberto": float(conta.valor_aberto),
            "valor_aberto_formatado": format_currency(conta.valor_aberto),
            "valor_pago": float(conta.valor_original - conta.valor_aberto),
            "valor_pago_formatado": format_currency(
                conta.valor_original - conta.valor_aberto
            ),
            "data_emissao": conta.data_emissao.isoformat(),
            "data_emissao_br": formatar_data_br(conta.data_emissao),
            "data_vencimento": conta.data_vencimento.isoformat(),
            "data_vencimento_br": formatar_data_br(conta.data_vencimento),
            "data_pagamento": (
                conta.data_pagamento.isoformat() if conta.data_pagamento else None
            ),
            "data_pagamento_br": (
                formatar_data_br(conta.data_pagamento) if conta.data_pagamento else None
            ),
            "status": conta.status.value,
            "status_label": conta.status.name.capitalize(),
            "observacoes": conta.observacoes,
            "nota_fiscal_id": conta.nota_fiscal_id,
        }

        # Produtos da nota fiscal (se houver)
        produtos = []
        if conta.nota_fiscal:
            for item in conta.nota_fiscal.itens:
                produtos.append(
                    {
                        "produto_id": item.produto_id,
                        "nome": item.produto.nome,
                        "quantidade": float(item.quantidade),
                        "quantidade_formatada": format_number(item.quantidade),
                        "valor_unitario": float(item.valor_unitario),
                        "valor_unitario_formatado": format_currency(
                            item.valor_unitario
                        ),
                        "valor_total": float(item.valor_total),
                        "valor_total_formatado": format_currency(item.valor_total),
                        "unidade": (
                            item.produto.unidade.value if item.produto.unidade else "un"
                        ),
                        "estoque_origem": (
                            item.estoque_origem.value if item.estoque_origem else "N/A"
                        ),
                    }
                )

        # Histórico de pagamentos
        pagamentos = []
        for pagamento in conta.pagamentos:
            pagamentos.append(
                {
                    "id": pagamento.id,
                    "valor_pago": float(pagamento.valor_pago),
                    "valor_pago_formatado": format_currency(pagamento.valor_pago),
                    "data_pagamento": pagamento.data_pagamento.isoformat(),
                    "data_pagamento_br": formatar_data_br(pagamento.data_pagamento),
                    "forma_pagamento": pagamento.forma_pagamento.value,
                    "forma_pagamento_label": pagamento.forma_pagamento.name.replace(
                        "_", " "
                    ).title(),
                    "observacoes": pagamento.observacoes,
                    "caixa_id": pagamento.caixa_id,
                    "operador": (
                        pagamento.caixa.operador.nome
                        if pagamento.caixa and pagamento.caixa.operador
                        else "N/A"
                    ),
                }
            )

        return jsonify(
            {
                "success": True,
                "conta": conta_info,
                "produtos": produtos,
                "pagamentos": pagamentos,
                "total_produtos": len(produtos),
                "total_pagamentos": len(pagamentos),
            }
        )

    except Exception as e:
        logger.error(f"Erro ao obter detalhes da conta: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/clientes", methods=["POST"])
@login_required
@admin_required
def criar_cliente():
    try:
        data = request.get_json()
        cliente_data = ClienteCreate(
            nome=data["nome"],
            documento=data.get("documento"),
            telefone=data.get("telefone"),
            email=data.get("email"),
            endereco=data.get("endereco"),
            criado_em=datetime.now(tz=ZoneInfo("America/Sao_Paulo")),
            ativo=True,
        )

        cliente = create_cliente(db.session, cliente_data)

        logger.info(f"Cliente {cliente.nome} criado por usuário {current_user.nome}")
        return jsonify(
            {
                "success": True,
                "message": "Cliente criado com sucesso",
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "documento": cliente.documento,
                    "telefone": cliente.telefone,
                    "email": cliente.email,
                    "ativo": cliente.ativo,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/clientes/<int:cliente_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_cliente(cliente_id):
    try:
        data = request.get_json()

        cliente_data = ClienteUpdate(
            nome=data.get("nome"),
            documento=data.get("documento"),
            telefone=data.get("telefone"),
            email=data.get("email"),
            endereco=data.get("endereco"),
            ativo=data.get("ativo"),
        )

        cliente = update_cliente(db.session, cliente_id, cliente_data)

        logger.info(f"Cliente {cliente.id} atualizado por usuário {current_user.nome}")
        logger.info(f"Dados do cliente {cliente.id} atualizados: {cliente_data}")

        return jsonify(
            {
                "success": True,
                "message": "Cliente atualizado com sucesso",
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "documento": cliente.documento,
                    "telefone": cliente.telefone,
                    "email": cliente.email,
                    "ativo": cliente.ativo,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao atualizar cliente: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/clientes/<int:cliente_id>", methods=["GET"])
@login_required
@admin_required
def obter_cliente(cliente_id):
    try:
        cliente = get_cliente(db.session, cliente_id)
        if not cliente:
            return jsonify({"success": False, "message": "Cliente não encontrado"}), 404
        logger.info(f"Cliente {cliente_id} obtido por usuário {current_user.nome}")
        return jsonify(
            {
                "success": True,
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "documento": cliente.documento,
                    "telefone": cliente.telefone,
                    "email": cliente.email,
                    "endereco": cliente.endereco,
                    "ativo": cliente.ativo,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao obter cliente: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/clientes/<int:cliente_id>", methods=["DELETE"])
@login_required
@admin_required
def remover_cliente(cliente_id):
    try:
        delete_cliente(db.session, cliente_id)
        logger.info(f"Cliente {cliente_id} removido por usuário {current_user.nome}")
        return jsonify({"success": True, "message": "Cliente removido com sucesso"})
    except Exception as e:
        logger.error(f"Erro ao remover cliente: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


# ===== Produto Routes =====
@admin_bp.route("/produtos", methods=["GET"])
@login_required
@admin_required
def listar_produtos():
    try:
        search = request.args.get("search", "").lower()
        incluir_inativos = (
            request.args.get("incluir_inativos", "false").lower() == "true"
        )

        produtos = get_produtos(db.session, incluir_inativos=incluir_inativos)

        result = []
        for produto in produtos:
            if search and (
                search not in produto.nome.lower()
                and search not in produto.tipo.lower()
            ):
                continue

            result.append(
                {
                    "id": produto.id,
                    "codigo": produto.codigo or "",
                    "nome": produto.nome,
                    "tipo": produto.tipo,
                    "unidade": produto.unidade.value,
                    "valor": f"R$ {produto.valor_unitario:,.2f}",
                    "estoque_loja": f"{produto.estoque_loja:,.2f}",
                    "estoque_deposito": f"{produto.estoque_deposito:,.2f}",
                    "estoque_fabrica": f"{produto.estoque_fabrica:,.2f}",
                    "marca": produto.marca or "",
                    "ativo": produto.ativo,
                }
            )

        return jsonify({"success": True, "produtos": result})
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/produtos/pdf", methods=["GET"])
@login_required
@admin_required
def relatorio_produtos_pdf():
    try:
        search = request.args.get("search", "").lower()
        incluir_inativos = (
            request.args.get("incluir_inativos", "false").lower() == "true"
        )

        produtos = get_produtos(db.session, incluir_inativos=incluir_inativos)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=5 * mm,
            bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # -------------------- Cabeçalho --------------------
        logo_path = os.path.join(current_app.root_path, "static", "assets", "logo.jpeg")

        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=100 * mm, height=25 * mm))
            elements.append(Spacer(1, 6))

        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
        elements.append(Paragraph("📦 Relatório Geral de Produtos", header_style))
        elements.append(Spacer(1, -20))
        elements.append(
            Table(
                [["" * 80]],
                colWidths=[170 * mm],
                style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.black)],
            )
        )
        elements.append(Spacer(1, 12))

        # -------------------- Funções auxiliares --------------------
        def formatar_numero_br(valor):
            return (
                f"{float(valor):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        def formatar_moeda_br(valor):
            return (
                f"R$ {float(valor):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        def estoque_colorido(valor):
            cor = colors.green if float(valor) > 0 else colors.red
            return Paragraph(
                f'<font color="{cor.hexval()}">{formatar_numero_br(valor)}</font>',
                cell_style,
            )

        # -------------------- Tabela --------------------
        table_data = [
            [
                Paragraph("Código", styles["Normal"]),
                Paragraph("Nome", styles["Normal"]),
                Paragraph("Unidade", styles["Normal"]),
                Paragraph("Valor", styles["Normal"]),
                Paragraph("Depósito", styles["Normal"]),
                Paragraph("Loja", styles["Normal"]),
                Paragraph("Fábrica", styles["Normal"]),
            ]
        ]

        cell_style = ParagraphStyle(
            "Cell", fontSize=7, leading=9, alignment=TA_CENTER, wordWrap="CJK"
        )
        cell_left = ParagraphStyle("CellLeft", parent=cell_style, alignment=TA_LEFT)

        for produto in produtos:
            if search and (
                search not in produto.nome.lower()
                and search not in produto.tipo.lower()
            ):
                continue

            table_data.append(
                [
                    Paragraph(str(produto.codigo or ""), cell_style),
                    Paragraph(produto.nome, cell_left),
                    Paragraph(produto.unidade.value, cell_style),
                    Paragraph(formatar_moeda_br(produto.valor_unitario), cell_style),
                    estoque_colorido(produto.estoque_deposito),
                    estoque_colorido(produto.estoque_loja),
                    estoque_colorido(produto.estoque_fabrica),
                ]
            )

        col_widths = [20 * mm, 55 * mm, 20 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm]
        produto_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = TableStyle(
            [
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E8B57")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )

        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add("BACKGROUND", (0, i), (-1, i), colors.whitesmoke)

        produto_table.setStyle(table_style)
        elements.append(produto_table)

        # -------------------- Rodapé --------------------
        elements.append(Spacer(1, 15))
        rodape = datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M")
        elements.append(
            Paragraph(
                rodape,
                ParagraphStyle(
                    "Rodape", fontSize=8, alignment=TA_RIGHT, textColor=colors.grey
                ),
            )
        )

        # -------------------- Marca d'água --------------------
        def marca_dagua(canvas, doc):
            canvas.saveState()
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(45)
            canvas.setFont("Helvetica-Bold", 60)
            canvas.setFillColorRGB(0.85, 0.85, 0.85, alpha=0.2)
            canvas.drawCentredString(0, 0, "CAVALCANTI RAÇÕES")
            canvas.restoreState()

        doc.build(elements, onFirstPage=marca_dagua, onLaterPages=marca_dagua)

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=False,
            mimetype="application/pdf",
            download_name="produtos.pdf",
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF de produtos: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/lotes/pdf", methods=["GET"])
@login_required
@admin_required
def gerar_pdf_lotes():
    try:
        produto_id = request.args.get("produto_id", type=int)
        data_inicio_str = request.args.get("data_inicio")
        data_fim_str = request.args.get("data_fim")
        data_unica_str = request.args.get("data")

        query = db.session.query(LoteEstoque).join(
            Produto, LoteEstoque.produto_id == Produto.id
        )

        if produto_id:
            query = query.filter(LoteEstoque.produto_id == produto_id)

        filtro_data_aplicado = False
        data_inicio = None
        data_fim = None
        data_unica = None

        if data_unica_str:
            try:
                data_unica = datetime.strptime(data_unica_str, "%Y-%m-%d").date()
                data_inicio = datetime.combine(data_unica, time.min)
                data_fim = datetime.combine(data_unica, time.max)
                filtro_data_aplicado = True
            except ValueError as e:
                logger.warning(
                    f"Formato de data inválido: {data_unica_str} - Erro: {e}"
                )

        elif data_inicio_str or data_fim_str:
            if data_inicio_str:
                try:
                    data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
                    data_inicio = datetime.combine(data_inicio, time.min)
                except ValueError as e:
                    logger.warning(
                        f"Formato de data início inválido: {data_inicio_str} - Erro: {e}"
                    )

            if data_fim_str:
                try:
                    data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
                    data_fim = datetime.combine(data_fim, time.max)
                except ValueError as e:
                    logger.warning(
                        f"Formato de data fim inválido: {data_fim_str} - Erro: {e}"
                    )

            if data_inicio or data_fim:
                filtro_data_aplicado = True
                if data_inicio and data_fim:
                    query = query.filter(
                        LoteEstoque.data_entrada.between(data_inicio, data_fim)
                    )
                elif data_inicio:
                    query = query.filter(LoteEstoque.data_entrada >= data_inicio)
                elif data_fim:
                    query = query.filter(LoteEstoque.data_entrada <= data_fim)

        if filtro_data_aplicado and data_unica_str:
            query = query.filter(
                LoteEstoque.data_entrada.between(data_inicio, data_fim)
            )

        lotes = query.order_by(Produto.nome.asc(), LoteEstoque.data_entrada.asc()).all()

        for i, lote in enumerate(lotes[:3]):
            logger.info(
                f"Lote {i+1}: Produto={lote.produto.nome if lote.produto else 'N/A'}, "
                f"Data={lote.data_entrada}, "
                f"Qtd={lote.quantidade_disponivel}, "
                f"Valor Venda={lote.produto.valor_unitario if lote.produto else 'N/A'}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=2 * mm,
            bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # -------------------- Cabeçalho --------------------
        logo_path = os.path.join(current_app.root_path, "static", "assets", "logo.jpeg")

        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=100 * mm, height=25 * mm))
            elements.append(Spacer(1, 6))

        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
        )

        titulo = "Entradas no Estoque"
        info_filtros = []

        if produto_id:
            produto_filtrado = Produto.query.get(produto_id)
            if produto_filtrado:
                info_filtros.append(f"Produto: {produto_filtrado.nome}")

        if filtro_data_aplicado:
            if data_unica_str:
                info_filtros.append(f"Data: {formatar_data_br2(data_unica_str)}")
            else:
                periodo = []
                if data_inicio_str:
                    periodo.append(f"De: {formatar_data_br2(data_inicio_str)}")
                if data_fim_str:
                    periodo.append(f"Até: {formatar_data_br2(data_fim_str)}")
                if periodo:
                    info_filtros.append(" ".join(periodo))

        if info_filtros:
            titulo = f"{titulo} - {' | '.join(info_filtros)}"

        elements.append(Paragraph(titulo, header_style))
        elements.append(Spacer(1, -20))
        elements.append(
            Table(
                [["" * 80]],
                colWidths=[170 * mm],
                style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.black)],
            )
        )
        elements.append(Spacer(1, 12))

        # -------------------- Informações do Filtro --------------------
        if info_filtros:
            filtro_style = ParagraphStyle(
                "Filtro",
                parent=styles["Normal"],
                fontSize=9,
                alignment=TA_LEFT,
                spaceAfter=6,
                textColor=colors.grey,
            )
            elements.append(
                Paragraph(
                    f"Filtros aplicados: {' | '.join(info_filtros)}", filtro_style
                )
            )
            elements.append(Spacer(1, 6))

        # -------------------- Tabela --------------------
        table_data = [
            [
                Paragraph("Produto", styles["Normal"]),
                Paragraph("Qtd Inicial", styles["Normal"]),
                Paragraph("Qtd Disponível", styles["Normal"]),
                Paragraph("Valor de Compra", styles["Normal"]),
                Paragraph("Valor de Venda", styles["Normal"]),
                Paragraph("Data Entrada", styles["Normal"]),
                Paragraph("Ativo", styles["Normal"]),
            ]
        ]

        cell_style = ParagraphStyle(
            "Cell", fontSize=7, leading=9, alignment=TA_CENTER, wordWrap="CJK"
        )
        cell_left = ParagraphStyle("CellLeft", parent=cell_style, alignment=TA_LEFT)

        def formatar_numero_br(valor):
            return (
                f"{float(valor):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        def formatar_moeda_br(valor):
            return (
                f"R$ {float(valor):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        for lote in lotes:
            produto_nome = lote.produto.nome if lote.produto else "Sem produto"
            qtd_inicial = formatar_numero_br(lote.quantidade_inicial)
            qtd_disp_valor = float(lote.quantidade_disponivel)
            qtd_disp_str = formatar_numero_br(qtd_disp_valor)

            # cor condicional
            cor_qtd = colors.green if qtd_disp_valor > 0 else colors.red
            qtd_disp_paragraph = Paragraph(
                f'<font color="{cor_qtd.hexval()}">{qtd_disp_str}</font>', cell_style
            )

            valor_unitario = formatar_moeda_br(lote.valor_unitario_compra)
            
            # VALOR DE VENDA
            valor_venda = ""
            if lote.produto and lote.produto.valor_unitario:
                valor_venda = formatar_moeda_br(lote.produto.valor_unitario)
            else:
                valor_venda = "N/A"
            
            data_entrada = lote.data_entrada.strftime("%d/%m/%Y")

            # regra solicitada: ativo depende da quantidade disponível
            ativo_str = "Sim" if qtd_disp_valor > 0 else "Não"

            table_data.append(
                [
                    Paragraph(produto_nome, cell_left),
                    Paragraph(qtd_inicial, cell_style),
                    qtd_disp_paragraph,
                    Paragraph(valor_unitario, cell_style),
                    Paragraph(valor_venda, cell_style),  # NOVA COLUNA
                    Paragraph(data_entrada, cell_style),
                    Paragraph(ativo_str, cell_style),
                ]
            )

        if len(table_data) == 1:
            table_data.append(
                [
                    Paragraph(
                        "Nenhum lote encontrado com os filtros aplicados", cell_left
                    ),
                    Paragraph("", cell_style),
                    Paragraph("", cell_style),
                    Paragraph("", cell_style),
                    Paragraph("", cell_style),  # NOVA COLUNA VAZIA
                    Paragraph("", cell_style),
                    Paragraph("", cell_style),
                ]
            )

        col_widths = [55 * mm, 25 * mm, 25 * mm, 30 * mm, 30 * mm, 25 * mm, 15 * mm]
        lotes_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = TableStyle(
            [
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E8B57")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )

        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add("BACKGROUND", (0, i), (-1, i), colors.whitesmoke)

        lotes_table.setStyle(table_style)
        elements.append(lotes_table)

        # -------------------- Resumo --------------------
        if len(lotes) > 0:
            total_lotes = len(lotes)
            total_ativos = sum(
                1 for lote in lotes if float(lote.quantidade_disponivel) > 0
            )

            resumo_style = ParagraphStyle(
                "Resumo",
                parent=styles["Normal"],
                fontSize=9,
                alignment=TA_LEFT,
                spaceBefore=12,
                textColor=colors.darkgreen,
            )

            resumo_text = (
                f"Resumo: {total_lotes} lote(s) encontrado(s) | {total_ativos} ativo(s)"
            )
            elements.append(Paragraph(resumo_text, resumo_style))
            logger.info(f"Resumo PDF: {resumo_text}")

        # -------------------- Marca d'água --------------------
        def marca_dagua(canvas, doc):
            canvas.saveState()
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(45)
            canvas.setFont("Helvetica-Bold", 60)
            canvas.setFillColorRGB(0.85, 0.85, 0.85, alpha=0.2)
            canvas.drawCentredString(0, 0, "CAVALCANTI RAÇÕES")
            canvas.restoreState()

        doc.build(elements, onFirstPage=marca_dagua, onLaterPages=marca_dagua)

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=False,
            mimetype="application/pdf",
            download_name="lotes.pdf",
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF de lotes: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/produtos", methods=["POST"])
@login_required
@admin_required
def criar_produto():
    try:
        if request.content_type and request.content_type.startswith(
            "multipart/form-data"
        ):
            form_data = request.form
            foto_file = request.files.get("foto")
        else:
            form_data = request.get_json() or {}
            foto_file = None

        usuario_id = current_user.id
        data_atual = datetime.now(ZoneInfo("America/Sao_Paulo"))

        nome = form_data.get("nome")
        unidade = form_data.get("unidade")

        if not nome or not unidade:
            return (
                jsonify(
                    {"success": False, "message": "Nome e unidade são obrigatórios"}
                ),
                400,
            )

        produto_existente = (
            db.session.query(Produto)
            .filter(
                func.lower(Produto.nome) == func.lower(nome),
                Produto.unidade == unidade,
                Produto.ativo.is_(True),
            )
            .first()
        )

        if produto_existente:
            estoque_loja_add = to_decimal_or_none(form_data.get("estoque_loja", 0))
            estoque_deposito_add = to_decimal_or_none(
                form_data.get("estoque_deposito", 0)
            )
            estoque_fabrica_add = to_decimal_or_none(
                form_data.get("estoque_fabrica", 0)
            )
            valor_unitario_compra = to_decimal_or_none(
                form_data.get("valor_unitario_compra", form_data.get("valor_unitario"))
            )

            update_data = {
                "estoque_loja": produto_existente.estoque_loja
                + (estoque_loja_add or 0),
                "estoque_deposito": produto_existente.estoque_deposito
                + (estoque_deposito_add or 0),
                "estoque_fabrica": produto_existente.estoque_fabrica
                + (estoque_fabrica_add or 0),
            }

            if valor_unitario_compra:
                update_data["valor_unitario_compra"] = valor_unitario_compra

            produto = update_produto(
                db.session, produto_existente.id, ProdutoUpdate(**update_data)
            )

            if foto_file and foto_file.filename:
                foto_path = save_product_photo(foto_file, current_app, produto.id)
                produto.foto = foto_path

            for tipo_estoque, qtd in [
                (TipoEstoque.loja, estoque_loja_add),
                (TipoEstoque.deposito, estoque_deposito_add),
                (TipoEstoque.fabrica, estoque_fabrica_add),
            ]:
                if qtd and qtd > 0:
                    criar_ou_atualizar_lote(
                        db.session,
                        produto_id=produto.id,
                        quantidade=qtd,
                        valor_unitario_compra=valor_unitario_compra,
                        data_entrada=data_atual,
                        observacao=f"Entrada em estoque {tipo_estoque.value}",
                    )
                    db.session.add(
                        MovimentacaoEstoque(
                            produto_id=produto.id,
                            usuario_id=usuario_id,
                            caixa_id=None,
                            tipo=TipoMovimentacao.entrada,
                            estoque_destino=tipo_estoque,
                            quantidade=qtd,
                            valor_unitario=0,
                            valor_unitario_compra=valor_unitario_compra,
                            data=data_atual,
                            observacao="Entrada de estoque",
                        )
                    )

            db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "message": "Produto existente atualizado com sucesso",
                    "produto": {
                        "id": produto.id,
                        "nome": produto.nome,
                        "tipo": produto.tipo,
                        "unidade": produto.unidade.value,
                        "valor_unitario": str(produto.valor_unitario),
                        "valor_unitario_compra": str(produto.valor_unitario_compra),
                        "valor_total_compra": str(produto.valor_total_compra),
                        "imcs": str(produto.imcs),
                        "estoque_loja": str(produto.estoque_loja),
                        "estoque_deposito": str(produto.estoque_deposito),
                        "estoque_fabrica": str(produto.estoque_fabrica),
                        "estoque_minimo": str(produto.estoque_minimo),
                        "foto": produto.foto,
                        "foto_url": (
                            get_product_photo_url(produto.foto, current_app)
                            if produto.foto
                            else None
                        ),
                        "action": "updated",
                    },
                }
            )

        valor_unitario = to_decimal_or_none(form_data.get("valor_unitario"))
        valor_unitario_compra = to_decimal_or_none(
            form_data.get("valor_unitario_compra", valor_unitario)
        )
        valor_total_compra = to_decimal_or_none(form_data.get("valor_total_compra", 0))
        imcs = to_decimal_or_none(form_data.get("imcs", 0))
        estoque_loja = to_decimal_or_none(form_data.get("estoque_loja", 0))
        estoque_deposito = to_decimal_or_none(form_data.get("estoque_deposito", 0))
        estoque_fabrica = to_decimal_or_none(form_data.get("estoque_fabrica", 0))
        estoque_minimo = to_decimal_or_none(form_data.get("estoque_minimo", 0))

        produto = create_produto(
            db.session,
            ProdutoCreate(
                codigo=form_data.get("codigo"),
                nome=nome,
                tipo=form_data.get("tipo"),
                marca=form_data.get("marca"),
                unidade=unidade,
                valor_unitario=valor_unitario,
                valor_unitario_compra=valor_unitario_compra,
                valor_total_compra=valor_total_compra,
                imcs=imcs,
                estoque_loja=estoque_loja,
                estoque_deposito=estoque_deposito,
                estoque_fabrica=estoque_fabrica,
                estoque_minimo=estoque_minimo,
                estoque_maximo=None,
                ativo=True,
                foto=None,
            ),
        )

        db.session.flush()

        if foto_file and foto_file.filename:
            produto.foto = save_product_photo(foto_file, current_app, produto.id)

        for tipo_estoque, qtd in [
            (TipoEstoque.loja, estoque_loja),
            (TipoEstoque.deposito, estoque_deposito),
            (TipoEstoque.fabrica, estoque_fabrica),
        ]:
            if qtd and qtd > 0:
                criar_ou_atualizar_lote(
                    db.session,
                    produto_id=produto.id,
                    quantidade=qtd,
                    valor_unitario_compra=valor_unitario_compra,
                    data_entrada=data_atual,
                    observacao=f"Entrada inicial {tipo_estoque.value}",
                )
                db.session.add(
                    MovimentacaoEstoque(
                        produto_id=produto.id,
                        usuario_id=usuario_id,
                        caixa_id=None,
                        tipo=TipoMovimentacao.entrada,
                        estoque_destino=tipo_estoque,
                        quantidade=qtd,
                        valor_unitario=0,
                        valor_unitario_compra=valor_unitario_compra,
                        data=data_atual,
                        observacao="Entrada de estoque",
                    )
                )

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Produto criado com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "tipo": produto.tipo,
                    "unidade": produto.unidade.value,
                    "valor_unitario": str(produto.valor_unitario),
                    "valor_unitario_compra": str(produto.valor_unitario_compra),
                    "valor_total_compra": str(produto.valor_total_compra),
                    "imcs": str(produto.imcs),
                    "estoque_loja": str(produto.estoque_loja),
                    "estoque_deposito": str(produto.estoque_deposito),
                    "estoque_fabrica": str(produto.estoque_fabrica),
                    "estoque_minimo": str(produto.estoque_minimo),
                    "foto": produto.foto,
                    "foto_url": (
                        get_product_photo_url(produto.foto, current_app)
                        if produto.foto
                        else None
                    ),
                    "action": "created",
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar produto: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

@admin_bp.route("/dashboard/upload-xml", methods=["GET"])
@login_required
@admin_required
def entrada_produtos_xml():
    logger.info(f"Import de notas - Usuário: {current_user.nome}")
    return render_template("upload_xml.html")

@admin_bp.route("/nfe/processar-xml", methods=["POST"])
@login_required
@admin_required
def processar_xml():
    """
    Processa um XML de NFe, extrai produtos e salva todos os dados
    """
    try:
        # =========================
        # Validação do upload
        # =========================
        if 'xml_file' not in request.files:
            return jsonify({"success": False, "message": "Nenhum arquivo XML enviado"}), 400

        xml_file = request.files['xml_file']

        if not xml_file.filename:
            return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400

        if not xml_file.filename.lower().endswith('.xml'):
            return jsonify({"success": False, "message": "O arquivo deve ser um XML"}), 400

        # =========================
        # Parâmetros
        # =========================
        profit_percentage = to_decimal(
            request.form.get("profit_percentage", "30"),
            default=None,
            places=2
        )

        if profit_percentage is None or profit_percentage < 0:
            return jsonify({"success": False, "message": "Porcentagem de lucro inválida"}), 400

        stock_type = request.form.get("stock_type", "loja")
        product_category = request.form.get("product_category", "Ração")

        # =========================
        # Leitura do XML
        # =========================
        xml_content = xml_file.read().decode("utf-8")

        chave_acesso = extrair_chave_acesso(xml_content)
        if not chave_acesso:
            return jsonify({"success": False, "message": "Chave de acesso não encontrada no XML"}), 400

        nfe_existente = NFeXML.query.filter_by(chave_acesso=chave_acesso).first()
        if nfe_existente and nfe_existente.status_processamento == "processado":
            return jsonify({
                "success": False,
                "message": f"XML já processado (Chave: {chave_acesso})"
            }), 400

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            return jsonify({"success": False, "message": f"XML malformado: {e}"}), 400

        namespaces = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        dados_nfe = extrair_dados_nfe_completo(root, namespaces, chave_acesso)

        # =========================
        # Processamento dos produtos
        # =========================
        produtos_processados = []
        produtos_atualizados = 0
        novos_produtos = 0
        produtos_com_erro = 0

        usuario_id = current_user.id
        data_atual = datetime.now(ZoneInfo("America/Sao_Paulo"))

        for produto_xml in dados_nfe["produtos"]:
            try:
                # ---------- Valores ----------
                valor_compra = to_decimal(
                    produto_xml.get("valor_unitario_compra"),
                    default=None
                )

                if not valor_compra or valor_compra <= 0:
                    logger.warning(f"Valor de compra inválido: {produto_xml.get('nome_produto')}")
                    continue

                margem = profit_percentage / Decimal("100")
                valor_venda_calculado = valor_compra * (Decimal("1") + margem)
                valor_venda = arredondar_preco_venda(valor_venda_calculado)

                quantidade = to_decimal(
                    produto_xml.get("quantidade"),
                    default=Decimal("0"),
                    places=3
                )

                # ---------- Unidade ----------
                unidade_xml = produto_xml.get("unidade_comercial", "")
                unidade = determinar_unidade_produto(
                    unidade_xml,
                    produto_xml.get("nome_produto", "")
                )

                # ---------- Estoque ----------
                estoque_loja = quantidade if stock_type == "loja" else Decimal("0")
                estoque_deposito = quantidade if stock_type == "deposito" else Decimal("0")
                estoque_fabrica = quantidade if stock_type == "fabrica" else Decimal("0")

                nome_produto = produto_xml.get("nome_produto", "").strip()
                if not nome_produto:
                    continue

                # ---------- Produto existente ----------
                produto_existente = (
                    db.session.query(Produto)
                    .filter(
                        func.lower(Produto.nome) == func.lower(nome_produto),
                        Produto.unidade == unidade,
                        Produto.ativo.is_(True)
                    )
                    .first()
                )

                if produto_existente:
                    produto_existente.estoque_loja += estoque_loja
                    produto_existente.estoque_deposito += estoque_deposito
                    produto_existente.estoque_fabrica += estoque_fabrica
                    produto_existente.valor_unitario = valor_venda
                    produto_existente.valor_unitario_compra = valor_compra
                    produto_existente.atualizado_em = data_atual

                    produtos_atualizados += 1
                    status = "atualizado"
                    produto_ref = produto_existente

                else:
                    produto_ref = create_produto(
                        db.session,
                        ProdutoCreate(
                            codigo=produto_xml.get("codigo_produto", "").strip(),
                            nome=nome_produto,
                            tipo=product_category,
                            marca=extrair_marca_produto(nome_produto),
                            unidade=unidade,
                            valor_unitario=valor_venda,
                            valor_unitario_compra=valor_compra,
                            estoque_loja=estoque_loja,
                            estoque_deposito=estoque_deposito,
                            estoque_fabrica=estoque_fabrica,
                            estoque_minimo=Decimal("0"),
                            ativo=True,
                            foto=None
                        )
                    )
                    db.session.flush()

                    novos_produtos += 1
                    status = "criado"

                # ---------- Lote e movimentação ----------
                if quantidade > 0:
                    criar_ou_atualizar_lote(
                        db.session,
                        produto_id=produto_ref.id,
                        quantidade=quantidade,
                        valor_unitario_compra=valor_compra,
                        data_entrada=data_atual,
                        observacao=f"Entrada via XML NFe {chave_acesso}"
                    )

                    movimentacao = MovimentacaoEstoque(
                        produto_id=produto_ref.id,
                        usuario_id=usuario_id,
                        tipo=TipoMovimentacao.entrada,
                        estoque_destino=TipoEstoque[stock_type],
                        quantidade=quantidade,
                        valor_unitario=valor_venda,
                        valor_unitario_compra=valor_compra,
                        data=data_atual,
                        observacao=f"XML NFe {chave_acesso[:10]}..."
                    )
                    db.session.add(movimentacao)

                produtos_processados.append({
                    "nome": nome_produto,
                    "codigo": produto_ref.codigo,
                    "quantidade": float(quantidade),
                    "valor_compra": float(valor_compra),
                    "valor_venda": float(valor_venda),
                    "unidade": unidade.value,
                    "status": status
                })

            except Exception as e:
                produtos_com_erro += 1
                logger.error(f"Erro no produto {produto_xml.get('nome_produto')}: {e}", exc_info=True)

        # =========================
        # Salvar XML
        # =========================
        nfe_xml = salvar_nfe_xml_completo(
            db.session,
            chave_acesso,
            xml_content,
            dados_nfe
        )

        nfe_xml.status_processamento = "processado"
        nfe_xml.data_processamento = data_atual
        nfe_xml.sincronizado = False

        db.session.commit()

        return jsonify({
            "success": True,
            "chave_acesso": chave_acesso,
            "total_produtos": len(produtos_processados),
            "produtos_atualizados": produtos_atualizados,
            "novos_produtos": novos_produtos,
            "produtos_com_erro": produtos_com_erro,
            "produtos": produtos_processados
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro geral ao processar XML: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Erro interno ao processar XML"
        }), 500


@admin_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_produto(produto_id):
    try:
        # -----------------------------
        # Entrada de dados
        # -----------------------------
        if request.content_type and request.content_type.startswith(
            "multipart/form-data"
        ):
            form_data = request.form
            foto_file = request.files.get("foto")
            delete_foto = form_data.get("delete_foto") == "true"
        else:
            form_data = request.get_json() or {}
            foto_file = None
            delete_foto = form_data.get("delete_foto", False)

        produto = get_produto(db.session, produto_id)
        if not produto:
            return jsonify({"success": False, "message": "Produto não encontrado"}), 404

        update_fields = {}

        # -----------------------------
        # Campos básicos
        # -----------------------------
        for campo in ["nome", "tipo", "marca", "unidade", "ativo", "codigo"]:
            if campo in form_data:
                update_fields[campo] = form_data[campo]

        # -----------------------------
        # Campos monetários
        # -----------------------------
        for campo in [
            "valor_unitario",
            "valor_unitario_compra",
            "valor_total_compra",
            "imcs",
        ]:
            if campo in form_data:
                valor = to_decimal_2(form_data[campo])
                if valor is None:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": f"Valor inválido para {campo}",
                            }
                        ),
                        400,
                    )
                update_fields[campo] = valor

        # -----------------------------
        # Campos de estoque
        # -----------------------------
        for campo in [
            "estoque_loja",
            "estoque_deposito",
            "estoque_fabrica",
            "estoque_minimo",
            "estoque_maximo",
        ]:
            if campo in form_data:
                try:
                    valor = (
                        Decimal(str(form_data[campo]))
                        .quantize(Decimal("0.001"))
                        .quantize(Decimal("0.01"))
                    )
                    update_fields[campo] = valor
                except Exception:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": f"Valor inválido para {campo}",
                            }
                        ),
                        400,
                    )

        # -----------------------------
        # Conversões de unidade
        # -----------------------------
        for campo in ["peso_kg_por_saco", "pacotes_por_saco", "pacotes_por_fardo"]:
            if campo in form_data:
                try:
                    update_fields[campo] = (
                        Decimal(form_data[campo]).quantize(Decimal("0.001"))
                        if campo.startswith("peso")
                        else int(form_data[campo])
                    )
                except Exception:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": f"Valor inválido para {campo}",
                            }
                        ),
                        400,
                    )

        # -----------------------------
        # Atualizar dados do produto
        # -----------------------------
        produto_data = ProdutoUpdate(**update_fields)
        produto = update_produto(db.session, produto_id, produto_data)

        db.session.flush()  # 🔴 FUNDAMENTAL

        # -----------------------------
        # FOTO – REMOVER
        # -----------------------------
        if delete_foto and produto.foto:
            delete_product_photo(produto.foto, current_app)
            produto.foto = None

        # -----------------------------
        # FOTO – SUBSTITUIR / ADICIONAR
        # -----------------------------
        if foto_file and foto_file.filename:
            if produto.foto:
                delete_product_photo(produto.foto, current_app)

            produto.foto = save_product_photo(foto_file, current_app, produto.id)

        # -----------------------------
        # DESCONTOS
        # -----------------------------
        descontos_ids = []

        if "descontos[]" in form_data:
            descontos_ids = [int(i) for i in form_data.getlist("descontos[]") if i]
        elif isinstance(form_data.get("descontos"), list):
            descontos_ids = [int(i) for i in form_data["descontos"]]

        produto.descontos.clear()
        db.session.flush()

        for desconto_id in descontos_ids:
            desconto = buscar_desconto_by_id(db.session, desconto_id)
            if not desconto:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Desconto {desconto_id} não encontrado",
                        }
                    ),
                    400,
                )
            produto.descontos.append(desconto)

        # -----------------------------
        # COMMIT FINAL
        # -----------------------------
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Produto atualizado com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "foto": produto.foto,
                    "foto_url": (
                        get_product_photo_url(produto.foto, current_app)
                        if produto.foto
                        else None
                    ),
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar produto: {e}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/produtos/<int:produto_id>/entrada-estoque", methods=["POST"])
@login_required
@admin_required
def entrada_estoque(produto_id):
    try:
        data = request.get_json()
        usuario_id = current_user.id
        data_atual = datetime.now(ZoneInfo("America/Sao_Paulo"))

        produto = get_produto(db.session, produto_id)
        if not produto:
            logger.error(f"Produto de ID: {produto_id} não encontrado!")
            return jsonify({"success": False, "message": "Produto não encontrado"}), 404

        # Quantidades a adicionar
        estoque_loja_add = Decimal(data.get("estoque_loja", 0))
        estoque_deposito_add = Decimal(data.get("estoque_deposito", 0))
        estoque_fabrica_add = Decimal(data.get("estoque_fabrica", 0))
        valor_unitario_compra = Decimal(
            data.get(
                "valor_unitario_compra",
                produto.valor_unitario_compra or produto.valor_unitario,
            )
        )

        update_data = {}
        if estoque_loja_add > 0:
            update_data["estoque_loja"] = produto.estoque_loja + estoque_loja_add
        if estoque_deposito_add > 0:
            update_data["estoque_deposito"] = (
                produto.estoque_deposito + estoque_deposito_add
            )
        if estoque_fabrica_add > 0:
            update_data["estoque_fabrica"] = (
                produto.estoque_fabrica + estoque_fabrica_add
            )

        if not update_data:
            logger.error(f"Nenhuma quantidade válida informada")
            return (
                jsonify(
                    {"success": False, "message": "Nenhuma quantidade válida informada"}
                ),
                400,
            )

        # Atualizar produto
        produto_update = ProdutoUpdate(**update_data)
        produto = update_produto(db.session, produto.id, produto_update)

        # CRIAR/ATUALIZAR LOTES PARA CADA ENTRADA
        if estoque_loja_add > 0:
            criar_ou_atualizar_lote(
                db.session,
                produto_id=produto.id,
                quantidade=estoque_loja_add,
                valor_unitario_compra=valor_unitario_compra,
                data_entrada=data_atual,
                observacao="Entrada manual em estoque loja",
            )

        if estoque_deposito_add > 0:
            criar_ou_atualizar_lote(
                db.session,
                produto_id=produto.id,
                quantidade=estoque_deposito_add,
                valor_unitario_compra=valor_unitario_compra,
                data_entrada=data_atual,
                observacao="Entrada manual em estoque depósito",
            )

        if estoque_fabrica_add > 0:
            criar_ou_atualizar_lote(
                db.session,
                produto_id=produto.id,
                quantidade=estoque_fabrica_add,
                valor_unitario_compra=valor_unitario_compra,
                data_entrada=data_atual,
                observacao="Entrada manual em estoque fábrica",
            )

        # Registrar movimentações
        for destino, quantidade in [
            ("loja", estoque_loja_add),
            ("deposito", estoque_deposito_add),
            ("fabrica", estoque_fabrica_add),
        ]:
            if quantidade > 0:
                movimentacao = MovimentacaoEstoque(
                    produto_id=produto.id,
                    usuario_id=usuario_id,
                    caixa_id=None,
                    tipo=TipoMovimentacao.entrada,
                    estoque_destino=TipoEstoque[destino],
                    quantidade=quantidade,
                    valor_unitario=0,
                    valor_unitario_compra=valor_unitario_compra,
                    data=data_atual,
                    observacao="Entrada manual de estoque via edição de produto",
                )
                db.session.add(movimentacao)

        db.session.commit()
        logger.info("Entrada de estoque registrada com sucesso")
        return jsonify(
            {
                "success": True,
                "message": "Entrada de estoque registrada com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "estoque_loja": str(produto.estoque_loja),
                    "estoque_deposito": str(produto.estoque_deposito),
                    "estoque_fabrica": str(produto.estoque_fabrica),
                },
            }
        )

    except Exception as e:
        logger.exception(f"Erro: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 400


@admin_bp.route("/produtos/<int:produto_id>", methods=["GET"])
@login_required
@admin_required
def obter_produto(produto_id):
    try:
        produto = get_produto(db.session, produto_id)

        if not produto:
            return jsonify({"success": False, "message": "Produto não encontrado"}), 404

        # Obter todos os descontos disponíveis
        todos_descontos = buscar_todos_os_descontos(db.session)

        # Serializar descontos disponíveis
        descontos_disponiveis = []
        for desconto in todos_descontos:
            descontos_disponiveis.append(
                {
                    "id": desconto.id,
                    "identificador": desconto.identificador,
                    "descricao": desconto.descricao or "",
                    "tipo": desconto.tipo.name if desconto.tipo else None,
                    "valor": float(desconto.valor),
                    "quantidade_minima": float(desconto.quantidade_minima),
                    "quantidade_maxima": (
                        float(desconto.quantidade_maxima)
                        if desconto.quantidade_maxima
                        else None
                    ),
                    "valido_ate": (
                        desconto.valido_ate.isoformat() if desconto.valido_ate else None
                    ),
                    "ativo": desconto.ativo,
                }
            )

        # Serializar descontos do produto
        descontos_produto = []
        for desconto in produto.descontos:
            descontos_produto.append(
                {
                    "id": desconto.id,
                    "identificador": desconto.identificador,
                    "descricao": desconto.descricao or "",
                    "tipo": desconto.tipo.name if desconto.tipo else None,
                    "valor": float(desconto.valor),
                    "quantidade_minima": float(desconto.quantidade_minima),
                    "quantidade_maxima": (
                        float(desconto.quantidade_maxima)
                        if desconto.quantidade_maxima
                        else None
                    ),
                    "valido_ate": (
                        desconto.valido_ate.isoformat() if desconto.valido_ate else None
                    ),
                    "ativo": desconto.ativo,
                }
            )

        return jsonify(
            {
                "success": True,
                "produto": {
                    "id": produto.id,
                    "codigo": produto.codigo or "",
                    "nome": produto.nome,
                    "tipo": produto.tipo,
                    "marca": produto.marca or "",
                    "unidade": produto.unidade.value,
                    "foto": get_product_photo_url(produto.foto, current_app),
                    "valor_unitario": str(produto.valor_unitario),
                    "valor_unitario_compra": str(produto.valor_unitario_compra or 0),
                    "valor_total_compra": str(produto.valor_total_compra or 0),
                    "imcs": str(produto.imcs or 0),
                    "estoque_loja": f"{float(produto.estoque_loja or 0):.2f}",
                    "estoque_deposito": f"{float(produto.estoque_deposito or 0):.2f}",
                    "estoque_fabrica": f"{float(produto.estoque_fabrica or 0):.2f}",
                    "estoque_minimo": f"{float(produto.estoque_minimo or 0):.2f}",
                    "estoque_maximo": f"{float(produto.estoque_maximo or 0):.2f}",
                    "ativo": produto.ativo,
                    "descontos": descontos_produto,
                },
                "todos_descontos": descontos_disponiveis,
            }
        )
    except Exception as e:
        logger.error(f"Erro ao obter produto: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
@login_required
@admin_required
def remover_produto(produto_id):
    try:
        produto = db.session.query(Produto).get(produto_id)

        if not produto:
            logger.error(f"Produto {produto_id} não encontrado para remoção.")
            return jsonify({"success": False, "message": "Produto não encontrado"}), 404

        estoque_total = (
            float(produto.estoque_loja or 0)
            + float(produto.estoque_deposito or 0)
            + float(produto.estoque_fabrica or 0)
        )

        if estoque_total != 0:
            logger.warning(
                f"Não é possível remover o produto {produto_id}. Saldo em estoque: {estoque_total}"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Não é possível remover o produto. Ainda há saldo em estoque (mesmo que negativo).",
                    }
                ),
                400,
            )

        db.session.delete(produto)
        db.session.commit()

        logger.info(f"Produto {produto_id} removido por usuário {current_user.nome}")
        return jsonify({"success": True, "message": "Produto removido com sucesso"})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover produto: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao remover produto."}), 500


@admin_bp.route("/produtos/<int:produto_id>/movimentacao", methods=["POST"])
@login_required
@admin_required
def registrar_movimentacao_produto(produto_id):
    try:
        data = request.get_json()
        caixa = get_caixa_aberto(db.session)
        if not caixa:
            logger.error(
                f"Nenhum caixa aberto encontrado para movimentação do produto {produto_id}."
            )
            return (
                jsonify(
                    {"success": False, "message": "Nenhum caixa aberto encontrado"}
                ),
                400,
            )

        mov_data = MovimentacaoEstoqueCreate(
            produto_id=produto_id,
            usuario_id=current_user.id,
            cliente_id=data.get("cliente_id"),
            caixa_id=caixa.id,
            tipo=data["tipo"],
            quantidade=Decimal(data["quantidade"]),
            valor_unitario=Decimal(data["valor_unitario"]),
            valor_recebido=Decimal(data.get("valor_recebido", 0)),
            troco=Decimal(data.get("troco", 0)),
            forma_pagamento=data.get("forma_pagamento"),
            observacao=data.get("observacao"),
            estoque_origem=data.get("estoque_origem", TipoEstoque.loja),
            estoque_destino=data.get("estoque_destino", TipoEstoque.loja),
        )

        movimentacao = registrar_movimentacao(db.session, mov_data)

        logger.info(
            f"Movimentação {movimentacao.id} registrada por usuário {current_user.nome}"
        )
        return jsonify(
            {
                "success": True,
                "message": "Movimentação registrada com sucesso",
                "movimentacao": {
                    "id": movimentacao.id,
                    "data": movimentacao.data.strftime("%d/%m/%Y %H:%M"),
                    "tipo": movimentacao.tipo.value.capitalize(),
                    "quantidade": str(movimentacao.quantidade),
                    "valor_unitario": str(movimentacao.valor_unitario),
                    "produto": movimentacao.produto.nome,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao registrar movimentação: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/produtos/<int:produto_id>/transferir", methods=["POST"])
@login_required
@admin_required
def transferir_produto_estoque(produto_id):
    """
    Rota para transferir produto entre estoques.
    """
    try:
        data = request.get_json()

        campos_obrigatorios = [
            "usuario_id",
            "estoque_origem",
            "estoque_destino",
            "quantidade",
        ]
        for campo in campos_obrigatorios:
            if campo not in data:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Campo obrigatório faltando: {campo}",
                        }
                    ),
                    400,
                )

        produto_origem = Produto.query.get_or_404(produto_id)

        try:
            estoque_origem = TipoEstoque(data["estoque_origem"])
            estoque_destino = TipoEstoque(data["estoque_destino"])
        except ValueError as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Tipo de estoque inválido. Valores válidos: {[e.value for e in TipoEstoque]}",
                    }
                ),
                400,
            )

        try:
            quantidade = Decimal(str(data["quantidade"]))
        except:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Quantidade deve ser um número válido",
                    }
                ),
                400,
            )

        unidade_destino = None
        if "unidade_destino" in data and data["unidade_destino"] is not None:
            try:
                unidade_destino = UnidadeMedida(data["unidade_destino"])
            except ValueError as e:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Unidade de medida inválida. Valores válidos: {[e.value for e in UnidadeMedida]}",
                        }
                    ),
                    400,
                )

        dar_entrada_destino = data.get("dar_entrada_destino", True)
        observacao = data.get("observacao")

        transferencia = transferir_produto(
            produto_origem=produto_origem,
            usuario_id=data["usuario_id"],
            estoque_origem=estoque_origem,
            estoque_destino=estoque_destino,
            quantidade=quantidade,
            unidade_destino=unidade_destino,
            dar_entrada_destino=dar_entrada_destino,
            observacao=observacao,
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Transferência realizada com sucesso",
                    "transferencia": {
                        "id": transferencia.id,
                        "produto_origem_id": transferencia.produto_id,
                        "produto_destino_id": transferencia.produto_destino_id,
                        "quantidade_origem": str(transferencia.quantidade),
                        "quantidade_destino": str(transferencia.quantidade_destino),
                        "unidade_origem": transferencia.unidade_origem,
                        "unidade_destino": transferencia.unidade_destino,
                        "estoque_origem": transferencia.estoque_origem.value,
                        "estoque_destino": transferencia.estoque_destino.value,
                        "data": (
                            transferencia.data_criacao.isoformat()
                            if transferencia.data_criacao
                            else None
                        ),
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    except SQLAlchemyError as e:
        return (
            jsonify(
                {"success": False, "message": "Erro no banco de dados", "error": str(e)}
            ),
            500,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro interno no servidor",
                    "error": str(e),
                }
            ),
            500,
        )


# ===== Venda com Data Retroativa ====
@admin_bp.route("/api/vendas/retroativa", methods=["POST"])
@login_required
@admin_required
def api_registrar_venda_retroativa():
    if not request.is_json:
        logger.warning("Requisição inválida: Content-Type não é application/json")
        return (
            jsonify(
                {"success": False, "message": "Content-Type deve ser application/json"}
            ),
            400,
        )

    try:
        dados_venda = request.get_json()

        if dados_venda is None:
            logger.warning("Requisição inválida: JSON inválido ou não enviado")
            return (
                jsonify({"success": False, "message": "JSON inválido ou não enviado"}),
                400,
            )

        # Função auxiliar para converter e validar decimais
        def validar_decimal(valor, campo, max_digits=12, decimal_places=2):
            try:
                if valor is None:
                    return None
                str_valor = str(valor).strip()
                if not str_valor:
                    return None
                decimal_val = Decimal(str_valor).quantize(Decimal("0.01"))
                if abs(decimal_val.as_tuple().exponent) > decimal_places:
                    logger.warning(
                        f"Valor inválido para {campo}: mais de {decimal_places} casas decimais"
                    )
                    raise ValueError(
                        f"O campo {campo} deve ter no máximo {decimal_places} casas decimais"
                    )
                if len(str(decimal_val).replace(".", "").replace("-", "")) > max_digits:
                    logger.warning(
                        f"Valor inválido para {campo}: mais de {max_digits} dígitos no total"
                    )
                    raise ValueError(
                        f"O campo {campo} deve ter no máximo {max_digits} dígitos no total"
                    )
                return decimal_val
            except (ValueError, InvalidOperation) as e:
                logger.error(f"Erro ao validar campo {campo}: {str(e)}")
                raise ValueError(f"Valor inválido para {campo}: {str(e)}")

        # Campos obrigatórios
        required_fields = [
            "cliente_id",
            "itens",
            "pagamentos",
            "valor_total",
            "caixa_id",
            "data_emissao",
        ]
        for field in required_fields:
            if field not in dados_venda:
                logger.warning(f"Campo obrigatório faltando: {field}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Campo obrigatório faltando: {field}",
                        }
                    ),
                    400,
                )

        # Validar data de emissão
        try:
            data_emissao = datetime.strptime(
                dados_venda["data_emissao"], "%Y-%m-%d %H:%M:%S"
            )
            if data_emissao > datetime.now():
                logger.warning("Data de emissão inválida: não pode ser futura")
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Data de emissão não pode ser futura",
                        }
                    ),
                    400,
                )
        except ValueError:
            logger.warning("Formato de data inválido. Use YYYY-MM-DD HH:MM:SS")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Formato de data inválido. Use YYYY-MM-DD HH:MM:SS",
                    }
                ),
                400,
            )

        # Verificar caixa
        caixa = Caixa.query.get(dados_venda["caixa_id"])
        if not caixa:
            logger.warning(f"Caixa não encontrado: ID {dados_venda['caixa_id']}")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'Caixa não encontrado: ID {dados_venda["caixa_id"]}',
                    }
                ),
                404,
            )
        if caixa.status == "aberto":
            logger.warning("Para vendas retroativas, o caixa deve estar fechado")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Para vendas retroativas, o caixa deve estar fechado",
                    }
                ),
                400,
            )

        # Validar lista de itens
        if not isinstance(dados_venda["itens"], list) or len(dados_venda["itens"]) == 0:
            logger.warning("Lista de itens inválida ou vazia")
            return (
                jsonify(
                    {"success": False, "message": "Lista de itens inválida ou vazia"}
                ),
                400,
            )

        # Validar lista de pagamentos
        if (
            not isinstance(dados_venda["pagamentos"], list)
            or len(dados_venda["pagamentos"]) == 0
        ):
            logger.warning("Lista de pagamentos inválida ou vazia")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Lista de pagamentos inválida ou vazia",
                    }
                ),
                400,
            )

        # Converter e validar valores principais
        try:
            cliente_id = int(dados_venda["cliente_id"])
            valor_total = validar_decimal(dados_venda["valor_total"], "valor_total")
            total_descontos = validar_decimal(
                dados_venda.get("total_descontos", 0), "total_descontos"
            )

            # Validar cliente
            cliente = Cliente.query.get(cliente_id)
            if not cliente:
                logger.warning(f"Cliente não encontrado: ID {cliente_id}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Cliente não encontrado: ID {cliente_id}",
                        }
                    ),
                    404,
                )
        except ValueError as e:
            logger.error(f"Erro ao validar cliente: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 400

        # Validar itens
        itens_validados = []
        for item in dados_venda["itens"]:
            try:
                produto_id = int(item.get("produto_id"))
                produto = Produto.query.get(produto_id)
                if not produto:
                    logger.warning(f"Produto não encontrado: ID {produto_id}")
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": f"Produto não encontrado: ID {produto_id}",
                            }
                        ),
                        404,
                    )

                quantidade = validar_decimal(
                    item.get("quantidade"), "quantidade", decimal_places=3
                )
                valor_unitario = validar_decimal(
                    item.get("valor_unitario"), "valor_unitario"
                )
                valor_total_item = validar_decimal(
                    item.get("valor_total"), "valor_total"
                )
                desconto_aplicado = validar_decimal(
                    item.get("valor_desconto", 0), "valor_desconto"
                )

                if produto.estoque_loja < quantidade:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": f"Estoque insuficiente para {produto.nome} (disponível: {produto.estoque_loja}, solicitado: {quantidade})",
                            }
                        ),
                        400,
                    )

                itens_validados.append(
                    {
                        "produto": produto,
                        "quantidade": quantidade,
                        "valor_unitario": valor_unitario,
                        "valor_total": valor_total_item,
                        "desconto_aplicado": desconto_aplicado,
                        "tipo_desconto": item.get("desconto_info", {}).get("tipo"),
                    }
                )
            except ValueError as e:
                logger.error(f"Erro ao validar item: {str(e)}")
                return (
                    jsonify({"success": False, "message": f"Erro no item: {str(e)}"}),
                    400,
                )

        # Validar pagamentos
        pagamentos_validados = []
        valor_a_prazo = Decimal("0.00")
        valor_a_vista = Decimal("0.00")

        for pagamento in dados_venda["pagamentos"]:
            try:
                forma = pagamento.get("forma_pagamento")
                valor = validar_decimal(pagamento.get("valor"), "valor_pagamento")

                if forma == "a_prazo":
                    valor_a_prazo += valor
                else:
                    valor_a_vista += valor

                pagamentos_validados.append({"forma": forma, "valor": valor})
            except ValueError as e:
                logger.error(f"Erro ao validar pagamento: {str(e)}")
                return (
                    jsonify(
                        {"success": False, "message": f"Erro no pagamento: {str(e)}"}
                    ),
                    400,
                )

        # Verificar soma dos pagamentos
        soma_pagamentos = valor_a_vista + valor_a_prazo
        if abs(soma_pagamentos - valor_total) > Decimal("0.01"):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Valor recebido ({soma_pagamentos}) diferente do total da venda ({valor_total})",
                    }
                ),
                400,
            )

        # Criar nota fiscal
        nota = NotaFiscal(
            cliente_id=cliente.id,
            operador_id=current_user.id,
            caixa_id=caixa.id,
            data_emissao=data_emissao,
            valor_total=valor_total,
            valor_desconto=total_descontos,
            status=StatusNota.emitida,
            forma_pagamento=FormaPagamento.dinheiro,
            valor_recebido=valor_a_vista,
            troco=max(valor_a_vista - valor_total, Decimal("0.00")),
            a_prazo=valor_a_prazo > Decimal("0.00"),
            sincronizado=False,
        )

        # Criar entrega se existir
        if "endereco_entrega" in dados_venda and isinstance(
            dados_venda["endereco_entrega"], dict
        ):
            entrega_data = dados_venda["endereco_entrega"]
            entrega = Entrega(
                logradouro=entrega_data.get("logradouro", ""),
                numero=entrega_data.get("numero", ""),
                complemento=entrega_data.get("complemento", ""),
                bairro=entrega_data.get("bairro", ""),
                cidade=entrega_data.get("cidade", ""),
                estado=entrega_data.get("estado", ""),
                cep=entrega_data.get("cep", ""),
                instrucoes=entrega_data.get("instrucoes", ""),
                sincronizado=False,
            )
            db.session.add(entrega)
            db.session.flush()
            nota.entrega_id = entrega.id

        db.session.add(nota)
        db.session.flush()

        # Adicionar itens
        for item in itens_validados:
            item_nf = NotaFiscalItem(
                nota_id=nota.id,
                produto_id=item["produto"].id,
                estoque_origem=TipoEstoque.loja,
                quantidade=item["quantidade"],
                valor_unitario=item["valor_unitario"],
                valor_total=item["valor_total"],
                desconto_aplicado=item["desconto_aplicado"],
                tipo_desconto=(
                    TipoDesconto(item["tipo_desconto"])
                    if item["tipo_desconto"]
                    else None
                ),
                sincronizado=False,
            )
            db.session.add(item_nf)
            item["produto"].estoque_loja -= item["quantidade"]

        # Adicionar pagamentos
        pagamentos_ids = []
        for pagamento in pagamentos_validados:
            pagamento_nf = PagamentoNotaFiscal(
                nota_fiscal_id=nota.id,
                forma_pagamento=FormaPagamento(pagamento["forma"]),
                valor=pagamento["valor"],
                data=data_emissao,
                sincronizado=False,
            )
            db.session.add(pagamento_nf)
            db.session.flush()
            pagamentos_ids.append(pagamento_nf.id)

            if pagamento["forma"] != "a_prazo":
                financeiro = Financeiro(
                    tipo=TipoMovimentacao.entrada,
                    categoria=CategoriaFinanceira.venda,
                    valor=pagamento["valor"],
                    descricao=f"Pagamento venda NF #{nota.id}",
                    cliente_id=cliente.id,
                    caixa_id=caixa.id,
                    nota_fiscal_id=nota.id,
                    pagamento_id=pagamento_nf.id,
                    data=data_emissao,
                    sincronizado=False,
                )
                db.session.add(financeiro)

        # Criar conta a receber se houver valor a prazo
        if valor_a_prazo > Decimal("0.00"):
            conta_receber = ContaReceber(
                cliente_id=cliente.id,
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo NF #{nota.id}",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=data_emissao + timedelta(days=30),
                status=StatusPagamento.pendente,
                sincronizado=False,
            )
            db.session.add(conta_receber)

        # Definir forma de pagamento principal
        if len(pagamentos_validados) == 1:
            nota.forma_pagamento = FormaPagamento(pagamentos_validados[0]["forma"])

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Venda retroativa registrada com sucesso",
                    "nota_fiscal_id": nota.id,
                    "valor_total": float(valor_total.quantize(Decimal("0.01"))),
                    "valor_recebido": float(valor_a_vista.quantize(Decimal("0.01"))),
                    "troco": (
                        float(nota.troco.quantize(Decimal("0.01"))) if nota.troco else 0
                    ),
                    "valor_a_prazo": (
                        float(valor_a_prazo.quantize(Decimal("0.01")))
                        if valor_a_prazo > 0
                        else 0
                    ),
                    "data_emissao": data_emissao.strftime("%Y-%m-%d %H:%M:%S"),
                }
            ),
            201,
        )

    except SQLAlchemyError as e:
        logger.error(f"Erro ao registrar venda retroativa no banco: {str(e)}")
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro ao registrar venda retroativa no banco",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )

    except Exception as e:
        logger.error(f"Erro inesperado ao registrar venda retroativa: {str(e)}")
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro inesperado ao registrar venda retroativa",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )


# Rotas para carregar dados no modal
@admin_bp.route("/api/caixas/fechados", methods=["GET"])
@login_required
@admin_required
def api_caixas_fechados():
    try:
        caixas = (
            Caixa.query.filter_by(status="fechado")
            .order_by(Caixa.data_fechamento.desc())
            .all()
        )

        caixas_data = [
            {
                "id": caixa.id,
                "operador": caixa.operador.nome,
                "data_abertura": caixa.data_abertura.strftime("%d/%m/%Y %H:%M"),
                "data_fechamento": (
                    caixa.data_fechamento.strftime("%d/%m/%Y %H:%M")
                    if caixa.data_fechamento
                    else None
                ),
                "valor_abertura": float(caixa.valor_abertura),
                "valor_fechamento": (
                    float(caixa.valor_fechamento) if caixa.valor_fechamento else None
                ),
            }
            for caixa in caixas
        ]

        return jsonify({"success": True, "caixas": caixas_data})
    except Exception as e:
        logger.error(f"Erro ao buscar caixas fechados: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro ao buscar caixas fechados"}),
            500,
        )


@admin_bp.route("/caixas/<int:caixa_id>/fechar", methods=["POST"])
@login_required
@admin_required
def fechar_caixa(caixa_id):
    try:
        caixa = Caixa.query.get(caixa_id)
        if not caixa:
            return jsonify({"success": False, "message": "Caixa não encontrado"}), 404

        if caixa.status != StatusCaixa.aberto:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Somente caixas abertos podem ser fechados",
                    }
                ),
                400,
            )

        # Captura o valor de fechamento enviado no corpo da requisição
        data = request.get_json() or {}
        valor_fechamento = data.get("valor_fechamento")
        observacoes = data.get("observacoes", "")

        caixa.valor_fechamento = float(valor_fechamento)
        caixa.observacoes = observacoes
        caixa.data_fechamento = datetime.now(ZoneInfo("America/Sao_Paulo"))
        caixa.status = StatusCaixa.fechado
        caixa.admin_id = current_user.id  # registra quem fechou

        db.session.commit()
        logger.info(f"Caixa {caixa.id} fechado por usuário {current_user.nome}")

        return jsonify(
            {
                "success": True,
                "message": f"Caixa {caixa.id} fechado com sucesso",
                "data": {
                    "id": caixa.id,
                    "valor_fechamento": float(caixa.valor_fechamento),
                    "status": caixa.status.value,
                    "data_fechamento": caixa.data_fechamento.isoformat(),
                },
            }
        )
    except SQLAlchemyError as e:
        logger.error(f"Erro ao fechar caixa: {str(e)}")
        db.session.rollback()
        return (
            jsonify(
                {"success": False, "message": "Erro no banco de dados", "error": str(e)}
            ),
            500,
        )
    except Exception as e:
        logger.error(f"Erro ao fechar caixa: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Erro ao fechar caixa", "error": str(e)}
            ),
            500,
        )


@admin_bp.route("/api/clientes/ativos", methods=["GET"])
@login_required
@admin_required
def api_clientes_ativos():
    try:
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()

        clientes_data = [
            {
                "id": cliente.id,
                "nome": cliente.nome,
                "documento": cliente.documento or "",
                "telefone": cliente.telefone or "",
                "limite_credito": float(cliente.limite_credito),
            }
            for cliente in clientes
        ]

        return jsonify({"success": True, "clientes": clientes_data})
    except Exception as e:
        logger.error(f"Erro ao buscar clientes ativos: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao buscar clientes"}), 500


@admin_bp.route("/api/produtos/ativos", methods=["GET"])
@login_required
@admin_required
def api_produtos_ativos():
    try:
        produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()

        produtos_data = [
            {
                "id": produto.id,
                "codigo": produto.codigo or "",
                "nome": produto.nome,
                "valor_unitario": float(produto.valor_unitario),
                "estoque_loja": float(produto.estoque_loja),
                "unidade": produto.unidade.value,
                "marca": produto.marca or "",
                "tipo": produto.tipo,
            }
            for produto in produtos
        ]

        return jsonify({"success": True, "produtos": produtos_data})
    except Exception as e:
        logger.error(f"Erro ao buscar produtos ativos: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao buscar produtos"}), 500


# ===== Usuário Routes =====
@admin_bp.route("/usuarios", methods=["GET"])
@login_required
@admin_required
def listar_usuarios():
    try:
        search = request.args.get("search", "").lower()
        usuarios = get_usuarios(db.session)

        result = []
        for usuario in usuarios:
            if search and (
                search not in usuario.nome.lower()
                and search not in usuario.email.lower()
            ):
                continue

            conta_info = None
            if usuario.conta:
                saldos_por_forma = {}
                saldos_por_forma_formatado = {}

                for saldo in usuario.conta.saldos_forma_pagamento:
                    valor = float(saldo.saldo)
                    saldos_por_forma[saldo.forma_pagamento.value] = valor
                    saldos_por_forma_formatado[saldo.forma_pagamento.value] = (
                        locale.currency(valor, grouping=True)
                    )

                saldo_total = (
                    float(usuario.conta.saldo_total)
                    if usuario.conta.saldo_total
                    else 0.00
                )

                conta_info = {
                    "id": usuario.conta.id,
                    "saldo_total": saldo_total,  # numérico, para cálculos JS
                    "saldo_total_formatado": locale.currency(
                        saldo_total, grouping=True
                    ),  # string formatada
                    "saldos_por_forma": saldos_por_forma,
                    "saldos_por_forma_formatado": saldos_por_forma_formatado,
                    "atualizado_em": (
                        usuario.conta.atualizado_em.strftime("%d/%m/%Y %H:%M")
                        if usuario.conta.atualizado_em
                        else None
                    ),
                }

            result.append(
                {
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "tipo": usuario.tipo.value.capitalize(),
                    "status": "Ativo" if usuario.status else "Inativo",
                    "ultimo_acesso": (
                        usuario.ultimo_acesso.strftime("%d/%m/%Y %H:%M")
                        if usuario.ultimo_acesso
                        else "Nunca"
                    ),
                    "cpf": usuario.cpf,
                    "conta": conta_info,
                }
            )

        return jsonify({"success": True, "usuarios": result})
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
@login_required
@admin_required
def get_usuario(usuario_id):
    try:
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            logger.warning(f"Usuário não encontrado: ID {usuario_id}")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Usuário não encontrado",
                        "error": "not_found",
                    }
                ),
                404,
            )

        # Verificar se o tipo é um Enum antes de acessar .value
        tipo_usuario = (
            usuario.tipo.value if hasattr(usuario.tipo, "value") else usuario.tipo
        )

        # Formatar datas corretamente
        ultimo_acesso = (
            usuario.ultimo_acesso.strftime("%d/%m/%Y %H:%M")
            if usuario.ultimo_acesso
            else None
        )
        data_cadastro = (
            usuario.criado_em.strftime("%d/%m/%Y %H:%M") if usuario.criado_em else None
        )

        # Informações da conta
        conta_info = None
        if usuario.conta:
            saldos_por_forma = {}
            for saldo in usuario.conta.saldos_forma_pagamento:
                saldos_por_forma[saldo.forma_pagamento.value] = locale.currency(
                    float(saldo.saldo), grouping=True
                )

            conta_info = {
                "id": usuario.conta.id,
                "saldo_total": (
                    locale.currency(float(usuario.conta.saldo_total), grouping=True)
                    if usuario.conta.saldo_total
                    else 0.00
                ),
                "saldos_por_forma": saldos_por_forma,
                "atualizado_em": (
                    usuario.conta.atualizado_em.strftime("%d/%m/%Y %H:%M")
                    if usuario.conta.atualizado_em
                    else None
                ),
            }

        return jsonify(
            {
                "success": True,
                "usuario": {
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "cpf": usuario.cpf,
                    "tipo": tipo_usuario,
                    "status": bool(usuario.status),  # Garantir que é booleano
                    "ultimo_acesso": ultimo_acesso,
                    "data_cadastro": data_cadastro,
                    "observacoes": usuario.observacoes
                    or "",  # Garantir string vazia se None
                    "conta": conta_info,  # Nova informação da conta
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao carregar dados do usuário: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro interno ao carregar dados do usuário",
                    "error": str(e),
                }
            ),
            500,
        )


@admin_bp.route("/usuarios", methods=["POST"])
@login_required
@admin_required
def criar_usuario():
    try:
        data = request.get_json()

        usuario_data = UsuarioCreate(
            nome=data["nome"],
            cpf=data["cpf"],
            senha=data["senha"],
            tipo=data["tipo"],
            status=data.get("status", True),
            observacoes=data.get("observacoes"),
        )

        novo_usuario = create_user(db.session, usuario_data)
        logger.info(
            f"Usuário {novo_usuario.id} criado por administrador {current_user.nome}"
        )
        return jsonify(
            {
                "success": True,
                "message": "Usuário criado com sucesso",
                "usuario": {
                    "id": novo_usuario.id,
                    "nome": novo_usuario.nome,
                    "cpf": novo_usuario.cpf,
                    "tipo": novo_usuario.tipo.value,
                    "status": novo_usuario.status,
                    "observacoes": novo_usuario.observacoes,
                },
            }
        )

    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/usuarios/<int:usuario_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_usuario(usuario_id):
    try:
        data = request.get_json()

        # Verificar se foi enviada senha e confirmação
        if "senha" in data or "confirma_senha" in data:
            if "senha" not in data or "confirma_senha" not in data:
                raise ValueError(
                    "Para alterar a senha, ambos os campos 'senha' e 'confirma_senha' devem ser enviados"
                )
            if data["senha"] != data["confirma_senha"]:
                raise ValueError("As senhas não coincidem")

        # Criar o objeto de atualização removendo campos não relevantes
        update_data = {k: v for k, v in data.items() if k not in ["confirma_senha"]}

        usuario_data = UsuarioUpdate(**update_data)

        usuario = update_user(db.session, usuario_id, usuario_data)

        logger.info(
            f"Usuário {usuario.id} atualizado por administrador {current_user.nome}"
        )
        return jsonify(
            {
                "success": True,
                "message": "Usuário atualizado com sucesso",
                "usuario": {
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "cpf": usuario.cpf,
                    "tipo": usuario.tipo.value,
                    "status": usuario.status,
                    "observacoes": usuario.observacoes,
                },
            }
        )

    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@login_required
@admin_required
def remover_usuario(usuario_id):
    try:
        usuario = get_user_by_id(db.session, usuario_id)
        if not usuario:
            logger.warning(f"Usuário não encontrado para remoção: ID {usuario_id}")
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404

        db.session.delete(usuario)
        db.session.commit()
        logger.info(
            f"Usuário {usuario_id} removido por administrador {current_user.nome}"
        )
        return jsonify({"success": True, "message": "Usuário removido com sucesso"})

    except IntegrityError:
        logger.warning(
            f"Não é possível remover o usuário {usuario_id}. Ele está vinculado a caixas."
        )
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Não é possível remover o usuário. Ele está vinculado a um ou mais caixas.",
                }
            ),
            400,
        )

    except Exception as e:
        logger.error(f"Erro inesperado ao remover usuário: {str(e)}")
        db.session.rollback()
        traceback.print_exc()
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro inesperado ao remover o usuário. Tente novamente mais tarde.",
                }
            ),
            500,
        )


# ===== Financeiro Routes =====
@admin_bp.route("/financeiro", methods=["GET"])
@login_required
@admin_required
def listar_financeiro():
    try:
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        categoria = request.args.get("categoria")
        tipo = request.args.get("tipo")
        caixa_id = request.args.get("caixa_id")

        # Convert dates if provided
        dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d") if data_inicio else None
        dt_fim = datetime.strptime(data_fim, "%Y-%m-%d") if data_fim else None

        lancamentos = get_lancamentos_financeiros(
            db.session,
            tipo=tipo,
            categoria=categoria,
            data_inicio=dt_inicio,
            data_fim=dt_fim,
            caixa_id=int(caixa_id) if caixa_id else None,
        )

        receitas = 0
        despesas = 0

        result = []
        for lanc in lancamentos:
            valor = float(lanc.valor)
            if lanc.tipo == "entrada":
                receitas += valor
            else:
                despesas += valor

            result.append(
                {
                    "data": lanc.data.strftime("%d/%m/%Y"),
                    "tipo": lanc.tipo.value.capitalize(),
                    "categoria": lanc.categoria.value.capitalize(),
                    "valor": f"R$ {valor:,.2f}",
                    "descricao": lanc.descricao,
                    "nota": lanc.nota_fiscal_id or "-",
                    "cor": "success" if lanc.tipo == "entrada" else "danger",
                }
            )

        saldo = receitas - despesas

        return jsonify(
            {
                "success": True,
                "lancamentos": result,
                "resumo": {
                    "receitas": f"R$ {receitas:,.2f}",
                    "despesas": f"R$ {despesas:,.2f}",
                    "saldo": f"R$ {saldo:,.2f}",
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao listar lançamentos financeiros: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/financeiro", methods=["POST"])
@login_required
@admin_required
def criar_lancamento_financeiro():
    try:
        data = request.get_json()

        lancamento_data = FinanceiroCreate(
            tipo=data["tipo"],
            categoria=data["categoria"],
            valor=Decimal(data["valor"]),
            descricao=data.get("descricao", ""),
            data=datetime.now(tz=ZoneInfo("America/Sao_Paulo")),
            nota_fiscal_id=data.get("nota_fiscal_id"),
            cliente_id=data.get("cliente_id"),
            caixa_id=data.get("caixa_id"),
        )

        lancamento = create_lancamento_financeiro(db.session, lancamento_data)
        logger.info(
            f"Lançamento financeiro {lancamento.id} criado por usuário {current_user.nome}"
        )
        return jsonify(
            {
                "success": True,
                "message": "Lançamento financeiro criado com sucesso",
                "lancamento": {
                    "id": lancamento.id,
                    "tipo": lancamento.tipo.value,
                    "categoria": lancamento.categoria.value,
                    "valor": str(lancamento.valor),
                    "descricao": lancamento.descricao,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao criar lançamento financeiro: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/financeiro/<int:lancamento_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_lancamento_financeiro(lancamento_id):
    try:
        data = request.get_json()

        lancamento_data = FinanceiroUpdate(
            tipo=data.get("tipo"),
            categoria=data.get("categoria"),
            valor=Decimal(data["valor"]) if "valor" in data else None,
            descricao=data.get("descricao"),
        )

        lancamento = update_lancamento_financeiro(
            db.session, lancamento_id, lancamento_data
        )
        logger.info(
            f"Lançamento financeiro {lancamento.id} atualizado por usuário {current_user.nome}"
        )
        return jsonify(
            {
                "success": True,
                "message": "Lançamento financeiro atualizado com sucesso",
                "lancamento": {
                    "id": lancamento.id,
                    "tipo": lancamento.tipo.value,
                    "categoria": lancamento.categoria.value,
                    "valor": str(lancamento.valor),
                    "descricao": lancamento.descricao,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao atualizar lançamento financeiro: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/financeiro/<int:lancamento_id>", methods=["DELETE"])
@login_required
@admin_required
def remover_lancamento_financeiro(lancamento_id):
    try:
        delete_lancamento_financeiro(db.session, lancamento_id)
        logger.info(
            f"Lançamento financeiro {lancamento_id} removido por usuário {current_user.nome}"
        )
        return jsonify(
            {"success": True, "message": "Lançamento financeiro removido com sucesso"}
        )
    except Exception as e:
        logger.error(f"Erro ao remover lançamento financeiro: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


# ===== Nota Fiscal Routes =====
@admin_bp.route("/notas-fiscais", methods=["POST"])
@login_required
def criar_nota_fiscal():
    try:
        data = request.get_json()
        caixa = get_caixa_aberto(db.session)
        if not caixa:
            return (
                jsonify(
                    {"success": False, "message": "Nenhum caixa aberto encontrado"}
                ),
                400,
            )

        nota_data = {
            "cliente_id": data.get("cliente_id"),
            "operador_id": current_user.id,
            "caixa_id": caixa.id,
            "valor_total": Decimal(data["valor_total"]),
            "forma_pagamento": data["forma_pagamento"],
            "valor_recebido": Decimal(data.get("valor_recebido", data["valor_total"])),
            "troco": Decimal(data.get("troco", 0)),
            "observacao": data.get("observacao", ""),
            "itens": data["itens"],
        }

        nota = create_nota_fiscal(db.session, nota_data)
        logger.info(f"Nota fiscal {nota.id} criada por usuário {current_user.nome}")
        return jsonify(
            {
                "success": True,
                "message": "Nota fiscal criada com sucesso",
                "nota": {
                    "id": nota.id,
                    "numero": nota.id,
                    "data": nota.data_emissao.strftime("%d/%m/%Y %H:%M"),
                    "valor_total": str(nota.valor_total),
                    "cliente": nota.cliente.nome if nota.cliente else "Consumidor",
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao criar nota fiscal: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/notas-fiscais", methods=["GET"])
@login_required
@admin_required
def listar_notas_fiscais():
    try:
        notas = get_notas_fiscais(db.session)
        result = []
        for nota in notas:
            result.append(
                {
                    "id": nota.id,
                    "data": nota.data_emissao.strftime("%d/%m/%Y %H:%M"),
                    "cliente": nota.cliente.nome if nota.cliente else "Consumidor",
                    "valor": f"R$ {nota.valor_total:,.2f}",
                    "status": nota.status.value.capitalize(),
                    "forma_pagamento": nota.forma_pagamento.value.replace(
                        "_", " "
                    ).capitalize(),
                }
            )

        return jsonify({"success": True, "notas": result})

    except Exception as e:
        logger.error(f"Erro ao listar notas fiscais: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/notas-fiscais/<int:nota_id>", methods=["GET"])
@login_required
@admin_required
def detalhar_nota_fiscal(nota_id):
    try:
        nota = get_nota_fiscal(db.session, nota_id)
        if not nota:
            logger.warning(f"Nota fiscal não encontrada: ID {nota_id}")
            return (
                jsonify({"success": False, "message": "Nota fiscal não encontrada"}),
                404,
            )

        itens = []
        for item in nota.itens:
            itens.append(
                {
                    "produto": item.produto.nome,
                    "quantidade": str(item.quantidade),
                    "valor_unitario": f"R$ {item.valor_unitario:,.2f}",
                    "valor_total": f"R$ {item.valor_total:,.2f}",
                }
            )

        return jsonify(
            {
                "success": True,
                "nota": {
                    "id": nota.id,
                    "data": nota.data_emissao.strftime("%d/%m/%Y %H:%M"),
                    "cliente": nota.cliente.nome if nota.cliente else "Consumidor",
                    "valor_total": f"R$ {nota.valor_total:,.2f}",
                    "status": nota.status.value.capitalize(),
                    "forma_pagamento": nota.forma_pagamento.value.replace(
                        "_", " "
                    ).capitalize(),
                    "valor_recebido": f"R$ {nota.valor_recebido:,.2f}",
                    "troco": f"R$ {nota.troco:,.2f}",
                    "operador": nota.operador.nome,
                    "itens": itens,
                },
            }
        )
    except Exception as e:
        logger.error(f"Erro ao detalhar nota fiscal: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/transferencias")
@login_required
@admin_required
def listar_transferencias():
    try:
        transferencias = get_transferencias(db.session)
        result = []
        for transf in transferencias:
            result.append(
                {
                    "id": transf.id,
                    "data": transf.data.strftime("%d/%m/%Y %H:%M"),
                    "produto": transf.produto.nome,
                    "origem": transf.estoque_origem.value,
                    "destino": transf.estoque_destino.value,
                    "quantidade": f"{transf.quantidade:.2f}",
                    "usuario": transf.usuario.nome,
                    "observacao": transf.observacao or "",
                }
            )

        return jsonify({"success": True, "transferencias": result})
    except Exception as e:
        logger.error(f"Erro ao listar transferências: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/produtos/<int:produto_id>/calcular-conversao", methods=["POST"])
@login_required
@admin_required
def calcular_conversao(produto_id):
    try:
        data = request.get_json()
        quantidade = Decimal(str(data["quantidade"]))
        unidade_origem = data["unidade_origem"]
        unidade_destino = data["unidade_destino"]
        fator_personalizado = Decimal(str(data.get("fator_personalizado", 0))) or None

        produto = db.session.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            logger.warning(f"Produto não encontrado para conversão: ID {produto_id}")
            return jsonify({"success": False, "message": "Produto não encontrado"}), 404

        # Calcular fator de conversão
        if fator_personalizado and fator_personalizado > 0:
            fator_conversao = fator_personalizado
        else:
            fator_conversao = calcular_fator_conversao(
                produto, unidade_origem, unidade_destino
            )

        quantidade_destino = quantidade * fator_conversao
        logger.info(
            f"Conversão calculada para produto {produto_id} por usuário {current_user.nome}"
        )
        return jsonify(
            {
                "success": True,
                "quantidade_destino": float(quantidade_destino),
                "fator_conversao": float(fator_conversao),
                "mensagem": f"1 {unidade_origem} = {fator_conversao} {unidade_destino}",
            }
        )

    except Exception as e:
        logger.error(f"Erro ao calcular conversão: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.route("/descontos", methods=["POST"])
@login_required
@admin_required
def criar_desconto_route():
    dados = request.get_json()

    # Validação básica dos dados - mantendo os nomes das variáveis originais
    required_fields = [
        "identificador",
        "quantidade_minima",
        "quantidade_maxima",
        "valor_unitario_com_desconto",
    ]
    if not all(field in dados for field in required_fields):
        logger.warning("Campos obrigatórios faltando para criar desconto")
        return jsonify({"erro": "Campos obrigatórios faltando"}), 400

    try:
        session = Session(db.engine)
        # Mapeando os campos mantendo os nomes das variáveis originais
        dados_desconto = {
            "identificador": dados["identificador"],
            "quantidade_minima": dados["quantidade_minima"],
            "quantidade_maxima": dados.get("quantidade_maxima"),
            "valor": dados[
                "valor_unitario_com_desconto"
            ],  # Mapeando para o campo 'valor' do modelo
            "tipo": TipoDesconto.fixo,  # Definindo como fixo para manter compatibilidade
            "descricao": dados.get("descricao", ""),
            "valido_ate": dados.get("valido_ate"),
            "ativo": dados.get("ativo", True),
        }

        desconto = criar_desconto(session, dados_desconto)
        logger.info(
            f"Desconto {desconto.id} criado por administrador {current_user.nome}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "mensagem": "Desconto criado com sucesso",
                    "desconto": {
                        "id": desconto.id,
                        "identificador": desconto.identificador,
                        "quantidade_minima": float(desconto.quantidade_minima),
                        "quantidade_maxima": float(desconto.quantidade_maxima),
                        "valor_unitario_com_desconto": float(
                            desconto.valor
                        ),  # Retornando o valor como valor_unitario_com_desconto
                        "valido_ate": (
                            desconto.valido_ate.isoformat()
                            if desconto.valido_ate
                            else None
                        ),
                        "ativo": desconto.ativo,
                        "criado_em": desconto.criado_em.isoformat(),
                    },
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Erro ao criar desconto: {str(e)}")
        return jsonify({"success": False, "erro": str(e)}), 500
    finally:
        session.close()


@admin_bp.route("/descontos/produto/<int:produto_id>", methods=["GET"])
@login_required
def buscar_descontos_produto_route(produto_id):
    try:
        session = Session(db.engine)
        descontos = buscar_descontos_por_produto_id(session, produto_id)

        return (
            jsonify(
                {
                    "success": True,
                    "descontos": [
                        {
                            "id": d.id,
                            "produto_id": produto_id,  # Mantendo o nome do parâmetro
                            "produto_nome": d.produto.nome if d.produto else None,
                            "quantidade_minima": float(d.quantidade_minima),
                            "quantidade_maxima": float(d.quantidade_maxima),
                            "valor_unitario_com_desconto": float(
                                d.valor
                            ),  # Mapeando valor para valor_unitario_com_desconto
                            "valido_ate": (
                                d.valido_ate.isoformat() if d.valido_ate else None
                            ),
                            "ativo": d.ativo,
                            "criado_em": d.criado_em.isoformat(),
                        }
                        for d in descontos
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Erro ao buscar descontos para o produto {produto_id}: {str(e)}")
        return jsonify({"success": False, "erro": str(e)}), 500
    finally:
        session.close()


@admin_bp.route("/descontos/<int:desconto_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_desconto_route(desconto_id):
    dados = request.get_json()

    try:
        session = Session(db.engine)
        # Mapeando os campos mantendo os nomes das variáveis originais
        dados_atualizacao = {
            "identificador": dados.get("identificador"),
            "quantidade_minima": dados.get("quantidade_minima"),
            "quantidade_maxima": dados.get("quantidade_maxima"),
            "valor": dados.get(
                "valor_unitario_com_desconto"
            ),  # Mapeando para o campo 'valor' do modelo
            "descricao": dados.get("descricao"),
            "valido_ate": dados.get("valido_ate"),
            "ativo": dados.get("ativo"),
        }

        desconto = atualizar_desconto(session, desconto_id, dados_atualizacao)

        if not desconto:
            logger.warning(f"Desconto não encontrado: ID {desconto_id}")
            return jsonify({"success": False, "erro": "Desconto não encontrado"}), 404
        logger.info(
            f"Desconto {desconto.id} atualizado por administrador {current_user.nome}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "mensagem": "Desconto atualizado com sucesso",
                    "desconto": {
                        "id": desconto.id,
                        "identificador": desconto.identificador,
                        "descricao": desconto.descricao,
                        "quantidade_minima": float(desconto.quantidade_minima),
                        "quantidade_maxima": float(desconto.quantidade_maxima),
                        "valor_unitario_com_desconto": float(
                            desconto.valor
                        ),  # Mapeando valor para valor_unitario_com_desconto
                        "valido_ate": (
                            desconto.valido_ate.isoformat()
                            if desconto.valido_ate
                            else None
                        ),
                        "ativo": desconto.ativo,
                        "atualizado_em": desconto.atualizado_em.isoformat(),
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Erro ao atualizar desconto: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "erro": "Erro interno ao tentar atualizar o desconto. Por favor, tente novamente mais tarde.",
                }
            ),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/descontos/<int:desconto_id>", methods=["DELETE"])
@login_required
@admin_required
def deletar_desconto_route(desconto_id):
    try:
        session = Session(db.engine)

        sucesso = deletar_desconto(session, desconto_id)

        if sucesso:
            logger.info(
                f"Desconto {desconto_id} deletado por administrador {current_user.nome}"
            )
            return (
                jsonify({"success": True, "message": "Desconto deletado com sucesso"}),
                200,
            )
        else:
            logger.warning(f"Desconto não encontrado para deleção: ID {desconto_id}")
            return (
                jsonify({"success": False, "message": "Desconto não encontrado"}),
                404,
            )

    except Exception as e:
        logger.error(f"Erro ao deletar desconto: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro interno ao tentar deletar o desconto. Por favor, tente novamente mais tarde.",
                }
            ),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/descontos", methods=["GET"])
@login_required
def listar_descontos_route():
    try:
        session = Session(db.engine)
        descontos = session.query(Desconto).order_by(Desconto.identificador).all()

        return (
            jsonify(
                {
                    "success": True,
                    "descontos": [
                        {
                            "id": d.id,
                            "identificador": d.identificador,
                            "descricao": d.descricao,
                            "quantidade_minima": float(d.quantidade_minima),
                            "quantidade_maxima": (
                                float(d.quantidade_maxima)
                                if d.quantidade_maxima
                                else None
                            ),
                            "valor": float(d.valor),
                            "tipo": d.tipo.name,
                            "valido_ate": (
                                d.valido_ate.isoformat() if d.valido_ate else None
                            ),
                            "ativo": d.ativo,
                            "criado_em": d.criado_em.isoformat(),
                        }
                        for d in descontos
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Erro ao listar descontos: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "erro": "Erro interno ao tentar listar os descontos. Por favor, tente novamente mais tarde.",
                }
            ),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/descontos/<int:desconto_id>", methods=["GET"])
@login_required
def buscar_desconto_por_id(desconto_id):
    try:
        session = Session(db.engine)
        desconto = session.query(Desconto).get(desconto_id)

        if not desconto:
            logger.warning(f"Desconto não encontrado: ID {desconto_id}")
            return jsonify({"success": False, "erro": "Desconto não encontrado"}), 404

        valido_ate_formatado = (
            desconto.valido_ate.strftime("%Y-%m-%d") if desconto.valido_ate else None
        )

        return (
            jsonify(
                {
                    "success": True,
                    "desconto": {
                        "id": desconto.id,
                        "identificador": desconto.identificador,
                        "quantidade_minima": float(desconto.quantidade_minima),
                        "quantidade_maxima": float(desconto.quantidade_maxima),
                        "valor_unitario_com_desconto": format_number(
                            desconto.valor
                        ),  # Mapeando valor para valor_unitario_com_desconto
                        "descricao": desconto.descricao,
                        "valido_ate": valido_ate_formatado,
                        "ativo": desconto.ativo,
                        "criado_em": formatar_data_br(desconto.criado_em),
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Erro ao buscar desconto por ID: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "erro": "Erro interno ao tentar buscar o desconto. Por favor, tente novamente mais tarde.",
                }
            ),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/descontos/<int:desconto_id>/produtos", methods=["GET"])
@login_required
def buscar_produtos_desconto_route(desconto_id):
    try:
        session = Session(db.engine)

        # Busca o desconto
        desconto = session.query(Desconto).get(desconto_id)

        if not desconto:
            logger.warning(f"Desconto não encontrado: ID {desconto_id}")
            return jsonify({"success": False, "erro": "Desconto não encontrado"}), 404

        # Busca os produtos associados a este desconto
        produtos = (
            session.query(Produto)
            .join(
                produto_desconto_association,
                Produto.id == produto_desconto_association.c.produto_id,
            )
            .filter(produto_desconto_association.c.desconto_id == desconto_id)
            .all()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "produtos": [
                        {
                            "id": p.id,
                            "codigo": p.codigo,
                            "nome": p.nome,
                            "tipo": p.tipo,
                            "ativo": p.ativo,
                        }
                        for p in produtos
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Erro ao buscar produtos do desconto {desconto_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "erro": "Erro interno ao tentar buscar os produtos do desconto. Por favor, tente novamente mais tarde.",
                }
            ),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/caixas")
@login_required
@admin_required
def get_caixas():
    session = Session(db.engine)

    # Parâmetros de filtro
    status = request.args.get("status")
    operador_id = request.args.get("operador_id")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    # Parâmetros de paginação
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)

    # Limita o máximo por página para evitar abusos
    if per_page > 100:
        per_page = 100

    query = session.query(Caixa).join(Usuario, Caixa.operador_id == Usuario.id)

    if status:
        try:
            status_enum = StatusCaixa(status)
            query = query.filter(Caixa.status == status_enum)
        except ValueError:
            pass  # ignora se status inválido

    if operador_id:
        try:
            operador_id_int = int(operador_id)
            query = query.filter(Caixa.operador_id == operador_id_int)
        except ValueError:
            pass  # ignora se operador_id inválido

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Caixa.data_abertura >= dt_inicio)
        except ValueError:
            pass

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            dt_fim = dt_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Caixa.data_abertura <= dt_fim)
        except ValueError:
            pass

    # Calcula o total antes da paginação
    total = query.count()

    # Aplica paginação
    caixas = (
        query.order_by(Caixa.data_abertura.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    data = []
    for c in caixas:
        # 1. CALCULA TOTAL DE ENTRADAS - SOMA TODAS AS FORMAS DE PAGAMENTO
        pagamentos_notas = (
            session.query(func.sum(PagamentoNotaFiscal.valor))
            .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
            .filter(
                NotaFiscal.caixa_id == c.id, NotaFiscal.status == StatusNota.emitida
            )
            .scalar()
            or 0.0
        )

        # Busca pagamentos de contas a receber
        pagamentos_contas = (
            session.query(func.sum(PagamentoContaReceber.valor_pago))
            .filter(PagamentoContaReceber.caixa_id == c.id)
            .scalar()
            or 0.0
        )

        total_entradas = float(pagamentos_notas) + float(pagamentos_contas)

        # 2. CALCULA TOTAL DE SAÍDAS - SOMENTE DESPESAS
        total_saidas = (
            session.query(func.sum(Financeiro.valor))
            .filter(
                Financeiro.caixa_id == c.id,
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria == CategoriaFinanceira.despesa,
            )
            .scalar()
            or 0.0
        )

        total_despesas = float(total_saidas)

        # 3. CALCULA VALOR FÍSICO (dinheiro) seguindo a mesma lógica
        pagamentos_dinheiro_notas = (
            session.query(func.sum(PagamentoNotaFiscal.valor))
            .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
            .filter(
                NotaFiscal.caixa_id == c.id,
                NotaFiscal.status == StatusNota.emitida,
                PagamentoNotaFiscal.forma_pagamento == FormaPagamento.dinheiro,
            )
            .scalar()
            or 0.0
        )

        pagamentos_dinheiro_contas = (
            session.query(func.sum(PagamentoContaReceber.valor_pago))
            .filter(
                PagamentoContaReceber.caixa_id == c.id,
                PagamentoContaReceber.forma_pagamento == FormaPagamento.dinheiro,
            )
            .scalar()
            or 0.0
        )

        valor_dinheiro = float(pagamentos_dinheiro_notas) + float(
            pagamentos_dinheiro_contas
        )

        # Aplica a mesma lógica de cálculo do valor físico
        valor_fisico = valor_dinheiro
        if c.valor_fechamento and c.valor_abertura:
            valor_abertura = float(c.valor_abertura)
            valor_fechamento = float(c.valor_fechamento)
            valor_fisico = max(
                (valor_dinheiro + valor_abertura) - valor_fechamento - total_despesas,
                0.0,
            )

        # 4. CALCULA VALOR DIGITAL
        formas_digitais = [
            FormaPagamento.pix_loja,
            FormaPagamento.pix_fabiano,
            FormaPagamento.pix_edfrance,
            FormaPagamento.pix_maquineta,
            FormaPagamento.cartao_debito,
            FormaPagamento.cartao_credito,
        ]

        pagamentos_digitais_notas = (
            session.query(func.sum(PagamentoNotaFiscal.valor))
            .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
            .filter(
                NotaFiscal.caixa_id == c.id,
                NotaFiscal.status == StatusNota.emitida,
                PagamentoNotaFiscal.forma_pagamento.in_(formas_digitais),
            )
            .scalar()
            or 0.0
        )

        pagamentos_digitais_contas = (
            session.query(func.sum(PagamentoContaReceber.valor_pago))
            .filter(
                PagamentoContaReceber.caixa_id == c.id,
                PagamentoContaReceber.forma_pagamento.in_(formas_digitais),
            )
            .scalar()
            or 0.0
        )

        valor_digital = float(pagamentos_digitais_notas) + float(
            pagamentos_digitais_contas
        )

        # 5. CALCULA A PRAZO
        pagamentos_prazo_notas = (
            session.query(func.sum(PagamentoNotaFiscal.valor))
            .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
            .filter(
                NotaFiscal.caixa_id == c.id,
                NotaFiscal.status == StatusNota.emitida,
                PagamentoNotaFiscal.forma_pagamento == FormaPagamento.a_prazo,
            )
            .scalar()
            or 0.0
        )

        a_prazo = float(pagamentos_prazo_notas)

        # 6. TOTAL DE CONTAS A RECEBER PAGAS
        total_contas_recebidas = float(pagamentos_contas)

        data.append(
            {
                "id": c.id,
                "operador": (
                    {"id": c.operador.id, "nome": c.operador.nome}
                    if c.operador
                    else None
                ),
                "data_abertura": (
                    c.data_abertura.isoformat() if c.data_abertura else None
                ),
                "data_fechamento": (
                    c.data_fechamento.isoformat() if c.data_fechamento else None
                ),
                "valor_abertura": float(c.valor_abertura) if c.valor_abertura else None,
                "valor_fechamento": (
                    float(c.valor_fechamento) if c.valor_fechamento else None
                ),
                "valor_confirmado": (
                    float(c.valor_confirmado) if c.valor_confirmado else None
                ),
                "status": c.status.value if c.status else None,
                # Novos campos calculados com a mesma lógica
                "total_vendas": total_entradas,  # Total de todas as entradas
                "total_contas_recebidas": total_contas_recebidas,
                "total_despesas": total_despesas,
                "valor_fisico": valor_fisico,
                "valor_digital": valor_digital,
                "a_prazo": a_prazo,
            }
        )

    # Fecha a sessão
    session.close()

    # Retorna informações de paginação
    return jsonify(
        {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1)
                // per_page,  # cálculo de total de páginas (arredonda para cima)
            },
        }
    )


@admin_bp.route("/usuarios/operadores")
@login_required
@admin_required
def get_operadores():
    """Retorna lista de operadores para o filtro"""
    session = Session(db.engine)

    try:
        operadores = (
            session.query(Usuario)
            .filter(Usuario.tipo == TipoUsuario.operador, Usuario.status == True)
            .order_by(Usuario.nome)
            .all()
        )

        data = []
        for op in operadores:
            data.append({"id": op.id, "nome": op.nome, "cpf": op.cpf})

        return jsonify({"success": True, "data": data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/caixas/pdf")
@login_required
@admin_required
def gerar_pdf_caixas_detalhado():
    session = Session(db.engine)
    try:
        status = request.args.get("status")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        operador_id = request.args.get("operador_id")

        query = session.query(Caixa).join(Usuario, Caixa.operador_id == Usuario.id)

        if status:
            try:
                status_enum = StatusCaixa(status)
                query = query.filter(Caixa.status == status_enum)
            except ValueError:
                pass  # ignora se status inválido

        if operador_id:
            try:
                operador_id_int = int(operador_id)
                query = query.filter(Caixa.operador_id == operador_id_int)
            except ValueError:
                pass  # ignora se operador_id inválido

        if data_inicio:
            try:
                dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                query = query.filter(Caixa.data_abertura >= dt_inicio)
            except ValueError:
                pass

        if data_fim:
            try:
                dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
                dt_fim = dt_fim.replace(hour=23, minute=59, second=59)
                query = query.filter(Caixa.data_abertura <= dt_fim)
            except ValueError:
                pass

        formas_prioridade_global = [
            "dinheiro",
            "pix_loja",
            "pix_fabiano",
            "pix_edfrance",
            "pix_maquineta",
            "cartao_credito",
            "cartao_debito",
            "a_prazo",
        ]
        caixas = query.order_by(Caixa.data_abertura.asc()).all()

        # Criar buffer para PDF
        buffer = BytesIO()

        # Configurar documento com as mesmas margens do primeiro relatório
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=10 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        # -------------------- Cabeçalho (mesmo estilo do primeiro relatório) --------------------
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
        )

        # Formatar datas para exibição
        periodo_text = ""
        if data_inicio and data_fim:
            data_inicio_fmt = datetime.strptime(data_inicio, "%Y-%m-%d").strftime(
                "%d/%m/%Y"
            )
            data_fim_fmt = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")
            periodo_text = f"Período: {data_inicio_fmt} a {data_fim_fmt}"
        elif data_inicio:
            data_inicio_fmt = datetime.strptime(data_inicio, "%Y-%m-%d").strftime(
                "%d/%m/%Y"
            )
            periodo_text = f"Período: A partir de {data_inicio_fmt}"
        elif data_fim:
            data_fim_fmt = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")
            periodo_text = f"Período: Até {data_fim_fmt}"
        else:
            periodo_text = "Período: Todos os caixas"

        elements.append(Paragraph("💰 Relatório de Controle de Caixas", header_style))
        elements.append(Paragraph(periodo_text, styles["Normal"]))

        # Status filter info
        if status:
            status_text = status.upper() if status else "TODOS"
            elements.append(Paragraph(f"Status: {status_text}", styles["Normal"]))

        elements.append(Spacer(1, 8))
        elements.append(
            Table(
                [[""]],
                colWidths=[170 * mm],
                style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.black)],
            )
        )
        elements.append(Spacer(1, 12))

        # -------------------- Resumo Executivo (mesmo estilo da primeira rota) --------------------
        # NOVO: Dicionário para armazenar totais por forma de pagamento por caixa
        totais_formas_pagamento_por_caixa = {}

        if caixas:
            # Cálculos para o resumo
            total_caixas = len(caixas)
            caixas_abertos = sum(1 for c in caixas if c.status == StatusCaixa.aberto)
            caixas_fechados = sum(1 for c in caixas if c.status == StatusCaixa.fechado)

            # Calcular totais gerais
            total_geral_entradas = 0
            total_geral_saidas = 0
            total_geral_estornos = 0
            total_geral_vendas = 0
            total_geral_contas_recebidas = 0
            total_pagamentos_consolidado = {}  # Para consolidar formas de pagamento

            # NOVO: Calcular estornos por forma de pagamento
            estornos_por_forma_global = {}

            for caixa in caixas:
                # Busca pagamentos de notas fiscais (VENDAS)
                pagamentos_notas = (
                    session.query(
                        PagamentoNotaFiscal.forma_pagamento,
                        func.sum(PagamentoNotaFiscal.valor).label("total"),
                    )
                    .join(
                        NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id
                    )
                    .filter(
                        NotaFiscal.caixa_id == caixa.id,
                        NotaFiscal.status == StatusNota.emitida,
                    )
                    .group_by(PagamentoNotaFiscal.forma_pagamento)
                    .all()
                )

                # Busca pagamentos de contas a receber (CONTAS RECEBIDAS)
                pagamentos_contas = (
                    session.query(
                        PagamentoContaReceber.forma_pagamento,
                        func.sum(PagamentoContaReceber.valor_pago).label("total"),
                    )
                    .filter(PagamentoContaReceber.caixa_id == caixa.id)
                    .group_by(PagamentoContaReceber.forma_pagamento)
                    .all()
                )

                # Calcula total de vendas (notas fiscais) e consolida formas de pagamento
                caixa_vendas = 0.0
                for forma, total in pagamentos_notas:
                    valor = float(total) if total else 0.0
                    total_pagamentos_consolidado[forma.value] = (
                        total_pagamentos_consolidado.get(forma.value, 0) + valor
                    )
                    caixa_vendas += valor
                total_geral_vendas += caixa_vendas

                # Calcula total de contas recebidas e consolida formas de pagamento
                caixa_contas_recebidas = 0.0
                for forma, total in pagamentos_contas:
                    valor = float(total) if total else 0.0
                    total_pagamentos_consolidado[forma.value] = (
                        total_pagamentos_consolidado.get(forma.value, 0) + valor
                    )
                    caixa_contas_recebidas += valor
                total_geral_contas_recebidas += caixa_contas_recebidas

                # Entradas brutas = vendas + contas recebidas
                caixa_entradas_bruto = caixa_vendas + caixa_contas_recebidas

                # Busca estornos (saida_estorno) para deduzir das entradas
                estornos = (
                    session.query(func.sum(Financeiro.valor))
                    .filter(
                        Financeiro.caixa_id == caixa.id,
                        Financeiro.tipo == TipoMovimentacao.saida_estorno,
                    )
                    .scalar()
                    or 0.0
                )

                estornos_valor = float(estornos)
                total_geral_estornos += estornos_valor

                # NOVO: Buscar informações sobre os estornos para distribuir por forma de pagamento
                # Como Financeiro não tem forma_pagamento, vamos distribuir proporcionalmente
                if estornos_valor > 0:
                    # Calcular proporção de cada forma de pagamento no caixa
                    total_caixa_formas = sum(
                        [float(total) for _, total in pagamentos_notas]
                        + [float(total) for _, total in pagamentos_contas]
                    )

                    if total_caixa_formas > 0:
                        # Distribuir estornos proporcionalmente às formas de pagamento
                        for forma, total in pagamentos_notas:
                            if total:
                                proporcao = float(total) / total_caixa_formas
                                estorno_forma = estornos_valor * proporcao
                                estornos_por_forma_global[forma.value] = (
                                    estornos_por_forma_global.get(forma.value, 0)
                                    + estorno_forma
                                )

                        for forma, total in pagamentos_contas:
                            if total:
                                proporcao = float(total) / total_caixa_formas
                                estorno_forma = estornos_valor * proporcao
                                estornos_por_forma_global[forma.value] = (
                                    estornos_por_forma_global.get(forma.value, 0)
                                    + estorno_forma
                                )

                # Entradas líquidas (entradas brutas - estornos)
                entradas_liquidas = caixa_entradas_bruto - estornos_valor
                total_geral_entradas += entradas_liquidas

                # Calcula total de saídas (somente despesas, excluindo estornos)
                caixa_saidas = (
                    session.query(func.sum(Financeiro.valor))
                    .filter(
                        Financeiro.caixa_id == caixa.id,
                        Financeiro.tipo == TipoMovimentacao.saida,
                        Financeiro.categoria == CategoriaFinanceira.despesa,
                    )
                    .scalar()
                    or 0.0
                )

                total_geral_saidas += float(caixa_saidas)

            saldo_geral = total_geral_entradas - total_geral_saidas

            # Tabela de resumo com fontes maiores
            resumo_data = [
                [
                    "Total Caixas",
                    " Abertos",
                    " Fechados",
                    "Total Entradas Líq.",
                    "Total Saídas",
                    "Total - Saídas",
                ],
                [
                    str(total_caixas),
                    str(caixas_abertos),
                    str(caixas_fechados),
                    formatarMoeda(total_geral_entradas),
                    formatarMoeda(total_geral_saidas),
                    formatarMoeda(saldo_geral),
                ],
            ]

            resumo_table = Table(
                resumo_data,
                colWidths=[25 * mm, 25 * mm, 25 * mm, 35 * mm, 35 * mm, 35 * mm],
            )
            resumo_style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONT", (0, 1), (-1, 1), "Helvetica", 10),
                ]
            )
            resumo_table.setStyle(resumo_style)
            elements.append(resumo_table)

            # Detalhamento das entradas com fontes maiores
            detalhes_entradas_data = [
                ["Detalhamento das Entradas", "Valor"],
                ["Total de Vendas (Notas Fiscais)", formatarMoeda(total_geral_vendas)],
                [
                    "Total de Contas Recebidas",
                    formatarMoeda(total_geral_contas_recebidas),
                ],
                ["Total Entradas Líquidas", formatarMoeda(total_geral_entradas)],
            ]

            detalhes_entradas_table = Table(
                detalhes_entradas_data, colWidths=[120 * mm, 60 * mm]
            )
            detalhes_entradas_style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONT", (0, 1), (-1, 1), "Helvetica", 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 3), (-1, 3), colors.lightgrey),
                    ("FONT", (0, 3), (-1, 3), "Helvetica-Bold", 9),
                ]
            )
            detalhes_entradas_table.setStyle(detalhes_entradas_style)
            elements.append(Spacer(1, 8))
            elements.append(detalhes_entradas_table)

            # NOVO: Totais por Forma de Pagamento com ESTORNOS DEDUZIDOS
            if total_pagamentos_consolidado:
                elements.append(Spacer(1, 12))

                # Título
                titulo_pagamentos = Paragraph(
                    "💳 Totais por Forma de Pagamento", styles["Heading2"]
                )
                elements.append(titulo_pagamentos)
                elements.append(Spacer(1, 8))

                # Preparar cabeçalho das colunas
                formas_colunas = []
                valores_brutos_colunas = []
                estornos_colunas = []
                valores_liquidos_colunas = []

                # Ordenar formas de pagamento por valor (maior para menor)
                formas_ordenadas = [
                    (f, total_pagamentos_consolidado.get(f, 0))
                    for f in formas_prioridade_global
                    if f in total_pagamentos_consolidado
                ]

                total_geral_bruto = 0
                total_geral_estornos_formas = 0
                total_geral_liquido = 0

                for forma, valor_bruto in formas_ordenadas:
                    if valor_bruto > 0:
                        forma_nome = forma.replace("_", " ").title()

                        # Calcular estorno para esta forma
                        estorno_forma = estornos_por_forma_global.get(forma, 0)

                        # Calcular valor líquido (bruto - estornos)
                        valor_liquido = valor_bruto - estorno_forma

                        # Só mostrar se pelo menos um dos valores for relevante
                        if valor_bruto > 0 or estorno_forma > 0 or valor_liquido > 0:
                            formas_colunas.append(forma_nome)
                            valores_brutos_colunas.append(formatarMoeda(valor_bruto))
                            estornos_colunas.append(formatarMoeda(estorno_forma))
                            valores_liquidos_colunas.append(
                                formatarMoeda(valor_liquido)
                            )

                            total_geral_bruto += valor_bruto
                            total_geral_estornos_formas += estorno_forma
                            total_geral_liquido += valor_liquido

                # Adicionar totais
                formas_colunas.append("TOTAL GERAL")
                valores_brutos_colunas.append(formatarMoeda(total_geral_bruto))
                estornos_colunas.append(formatarMoeda(total_geral_estornos_formas))
                valores_liquidos_colunas.append(formatarMoeda(total_geral_liquido))

                # Criar tabela com detalhes de estornos
                formas_data = [
                    ["Forma de Pagamento"] + formas_colunas,
                    ["Valor Bruto"] + valores_brutos_colunas,
                    ["Estornos"] + estornos_colunas,
                    ["Valor Líquido"] + valores_liquidos_colunas,
                ]

                # Calcular largura das colunas dinamicamente
                num_colunas = len(formas_colunas)
                if num_colunas > 0:
                    largura_total_disponivel = 180 * mm
                    largura_primeira_coluna = 40 * mm
                    largura_colunas_dados = (
                        largura_total_disponivel - largura_primeira_coluna
                    ) / num_colunas

                    col_widths = [largura_primeira_coluna] + [
                        largura_colunas_dados
                    ] * num_colunas

                    formas_pagamento_table = Table(formas_data, colWidths=col_widths)
                    formas_pagamento_style = TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("BACKGROUND", (-1, 0), (-1, -1), colors.lightgrey),
                            ("FONT", (-1, 0), (-1, -1), "Helvetica-Bold", 8),
                            # Cor para estornos (vermelho)
                            ("TEXTCOLOR", (0, 2), (-1, 2), colors.red),
                            ("FONT", (0, 2), (-1, 2), "Helvetica-Bold", 8),
                            # Cor para valor líquido (verde)
                            ("TEXTCOLOR", (0, 3), (-1, 3), colors.darkgreen),
                            ("FONT", (0, 3), (-1, 3), "Helvetica-Bold", 8),
                        ]
                    )
                    formas_pagamento_table.setStyle(formas_pagamento_style)
                    elements.append(formas_pagamento_table)

                    # Observação sobre estornos
                    observacao_style = ParagraphStyle(
                        "Observacao",
                        parent=styles["Normal"],
                        fontSize=8,
                        textColor=colors.grey,
                        alignment=TA_CENTER,
                    )
                    elements.append(Spacer(1, 8))
                    elements.append(
                        Paragraph(
                            "* Valores líquidos já descontados os estornos específicos de cada forma de pagamento",
                            observacao_style,
                        )
                    )

            elements.append(Spacer(1, 18))

        # -------------------- Detalhamento por Caixa --------------------
        if caixas:
            elements.append(Paragraph("📋 Detalhamento por Caixa", styles["Heading2"]))
            elements.append(Spacer(1, 8))

            # Variável para verificar se a soma dos caixas bate com o resumo
            soma_total_saidas_caixas = 0.0

            for idx, caixa in enumerate(caixas):
                # Cálculos exatos como na rota original
                operador_nome = (
                    caixa.operador.nome
                    if caixa.operador
                    else "Operador não identificado"
                )

                # Busca pagamentos de notas fiscais (VENDAS)
                pagamentos_notas = (
                    session.query(
                        PagamentoNotaFiscal.forma_pagamento,
                        func.sum(PagamentoNotaFiscal.valor).label("total"),
                    )
                    .join(
                        NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id
                    )
                    .filter(
                        NotaFiscal.caixa_id == caixa.id,
                        NotaFiscal.status == StatusNota.emitida,
                    )
                    .group_by(PagamentoNotaFiscal.forma_pagamento)
                    .all()
                )

                # Busca pagamentos de contas a receber (CONTAS RECEBIDAS)
                pagamentos_contas = (
                    session.query(
                        PagamentoContaReceber.forma_pagamento,
                        func.sum(PagamentoContaReceber.valor_pago).label("total"),
                    )
                    .filter(PagamentoContaReceber.caixa_id == caixa.id)
                    .group_by(PagamentoContaReceber.forma_pagamento)
                    .all()
                )

                # Calcula total de vendas e formas de pagamento
                total_vendas = 0.0
                formas_pagamento_vendas = {}

                for forma, total in pagamentos_notas:
                    valor = float(total) if total else 0.0
                    formas_pagamento_vendas[forma.value] = (
                        formas_pagamento_vendas.get(forma.value, 0) + valor
                    )
                    total_vendas += valor

                # Calcula total de contas recebidas e formas de pagamento
                total_contas_recebidas = 0.0
                formas_pagamento_contas = {}

                for forma, total in pagamentos_contas:
                    valor = float(total) if total else 0.0
                    formas_pagamento_contas[forma.value] = (
                        formas_pagamento_contas.get(forma.value, 0) + valor
                    )
                    total_contas_recebidas += valor

                # Combina todas as formas de pagamento (vendas + contas recebidas)
                todas_formas_pagamento = {}
                for forma, valor in formas_pagamento_vendas.items():
                    todas_formas_pagamento[forma] = (
                        todas_formas_pagamento.get(forma, 0) + valor
                    )
                for forma, valor in formas_pagamento_contas.items():
                    todas_formas_pagamento[forma] = (
                        todas_formas_pagamento.get(forma, 0) + valor
                    )

                # *** CORREÇÃO: CALCULAR VALOR EM DINHEIRO SEGUINDO A LÓGICA DA ROTA /caixas/<int:caixa_id>/financeiro ***
                valor_dinheiro_original = todas_formas_pagamento.get("dinheiro", 0.0)
                valor_fisico = valor_dinheiro_original

                # Aplica o mesmo cálculo da rota de financeiro
                if caixa.valor_abertura and caixa.valor_fechamento:
                    valor_abertura = float(caixa.valor_abertura)
                    valor_fechamento = float(caixa.valor_fechamento)

                    # Busca total de saídas (somente despesas) para o cálculo do dinheiro físico
                    total_saidas_dinheiro = (
                        session.query(func.sum(Financeiro.valor))
                        .filter(
                            Financeiro.caixa_id == caixa.id,
                            Financeiro.tipo == TipoMovimentacao.saida,
                            Financeiro.categoria == CategoriaFinanceira.despesa,
                        )
                        .scalar()
                        or 0.0
                    )

                    total_saidas_dinheiro = float(total_saidas_dinheiro)

                    # Cálculo do valor físico seguindo a mesma lógica da rota de financeiro
                    valor_fisico = (
                        (valor_dinheiro_original + valor_abertura)
                        - valor_fechamento
                        - total_saidas_dinheiro
                    )

                # *** CORREÇÃO: GARANTIR QUE DINHEIRO SEMPRE APAREÇA, MESMO QUE ZERO OU NEGATIVO ***
                # Atualiza o valor de dinheiro nas formas de pagamento com o cálculo correto
                todas_formas_pagamento["dinheiro"] = valor_fisico

                # Entradas brutas = vendas + contas recebidas
                total_entradas_bruto = total_vendas + total_contas_recebidas

                # Busca estornos (saida_estorno) para deduzir das entradas
                estornos = (
                    session.query(func.sum(Financeiro.valor))
                    .filter(
                        Financeiro.caixa_id == caixa.id,
                        Financeiro.tipo == TipoMovimentacao.saida_estorno,
                    )
                    .scalar()
                    or 0.0
                )

                estornos_valor = float(estornos)

                # Entradas líquidas (entradas brutas - estornos)
                total_entradas_liquidas = total_entradas_bruto - estornos_valor

                # Calcula total de saídas - SOMENTE DESPESAS
                total_saidas = (
                    session.query(func.sum(Financeiro.valor))
                    .filter(
                        Financeiro.caixa_id == caixa.id,
                        Financeiro.tipo == TipoMovimentacao.saida,
                        Financeiro.categoria == CategoriaFinanceira.despesa,
                    )
                    .scalar()
                    or 0.0
                )

                total_saidas = float(total_saidas)

                # *** CORREÇÃO: CALCULAR TOTAL - SAÍDAS CONSISTENTE COM O RESUMO ***
                # Total - Saídas = Entradas Líquidas - Saídas (mesma lógica do resumo)
                saldo_caixa = total_entradas_liquidas

                # Acumula para verificação
                soma_total_saidas_caixas += saldo_caixa

                # Status como texto simples sem HTML
                status_text = caixa.status.value.upper()

                # Tabela de informações do caixa
                caixa_data = [
                    [
                        "ID",
                        "Operador",
                        "Status",
                        "Data Abertura",
                        "Data Fechamento",
                        "Total",
                    ],
                    [
                        str(caixa.id),
                        (
                            operador_nome[:20] + "..."
                            if len(operador_nome) > 20
                            else operador_nome
                        ),
                        status_text,
                        (
                            caixa.data_abertura.strftime("%d/%m/%Y %H:%M")
                            if caixa.data_abertura
                            else "-"
                        ),
                        (
                            caixa.data_fechamento.strftime("%d/%m/%Y %H:%M")
                            if caixa.data_fechamento
                            else "Em aberto"
                        ),
                        formatarMoeda(saldo_caixa),
                    ],
                ]

                caixa_table = Table(
                    caixa_data,
                    colWidths=[15 * mm, 40 * mm, 25 * mm, 30 * mm, 30 * mm, 30 * mm],
                )

                # Aplicar cores diretamente no estilo da tabela
                caixa_style = TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("ALIGN", (1, 1), (1, -1), "LEFT"),
                        ("FONT", (0, 1), (-1, -1), "Helvetica", 10),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        (
                            "TEXTCOLOR",
                            (2, 1),
                            (2, 1),
                            (
                                colors.red
                                if caixa.status == StatusCaixa.aberto
                                else colors.darkgreen
                            ),
                        ),
                        (
                            "BACKGROUND",
                            (0, 1),
                            (-1, 1),
                            colors.whitesmoke if idx % 2 == 0 else colors.white,
                        ),
                    ]
                )
                caixa_table.setStyle(caixa_style)
                elements.append(caixa_table)

                # TABELA: FORMAS DE PAGAMENTO COMO COLUNAS + SAÍDAS
                # *** CORREÇÃO: GARANTIR QUE DINHEIRO SEMPRE APAREÇA, MESMO QUE ZERO OU NEGATIVO ***
                if todas_formas_pagamento:
                    # Preparar cabeçalho das colunas
                    formas_colunas = []
                    valores_colunas = []

                    # *** CORREÇÃO: GARANTIR QUE DINHEIRO SEMPRE APAREÇA PRIMEIRO ***
                    # Lista fixa de formas de pagamento para garantir ordem consistente
                    formas_prioridade = formas_prioridade_global

                    # Primeiro adiciona as formas de pagamento prioritárias
                    for forma in formas_prioridade:
                        if forma in todas_formas_pagamento:
                            forma_nome = forma.replace("_", " ").title()
                            formas_colunas.append(forma_nome)
                            valor = todas_formas_pagamento[forma]
                            valores_colunas.append(formatarMoeda(valor))

                    # Depois adiciona quaisquer outras formas de pagamento que possam existir
                    for forma, valor in todas_formas_pagamento.items():
                        if forma not in formas_prioridade:
                            forma_nome = forma.replace("_", " ").title()
                            formas_colunas.append(forma_nome)
                            valores_colunas.append(formatarMoeda(valor))

                    # Adicionar coluna de TOTAL
                    formas_colunas.append("TOTAL")
                    total_entradas = sum(
                        valor
                        for forma, valor in todas_formas_pagamento.items()
                        if forma != "a_prazo"
                    )
                    valores_colunas.append(formatarMoeda(total_entradas))

                    # Adicionar coluna de SAÍDAS
                    formas_colunas.append("SAÍDAS")
                    valores_colunas.append(formatarMoeda(total_saidas))

                    # Adicionar coluna de ESTORNOS
                    formas_colunas.append("Estornos")
                    valores_colunas.append(formatarMoeda(estornos_valor))

                    # Criar tabela com formas de pagamento como colunas
                    formas_data = [formas_colunas, valores_colunas]

                    # Calcular largura das colunas dinamicamente
                    num_colunas = len(formas_colunas)
                    largura_coluna = 190 * mm / num_colunas

                    formas_table = Table(
                        formas_data, colWidths=[largura_coluna] * num_colunas
                    )

                    # Encontrar os índices das colunas especiais
                    indice_saidas = (
                        formas_colunas.index("SAÍDAS")
                        if "SAÍDAS" in formas_colunas
                        else -1
                    )
                    indice_estornos = (
                        formas_colunas.index("Estornos")
                        if "Estornos" in formas_colunas
                        else -1
                    )
                    indice_total = (
                        formas_colunas.index("TOTAL")
                        if "TOTAL" in formas_colunas
                        else -1
                    )
                    indice_dinheiro = (
                        formas_colunas.index("Dinheiro")
                        if "Dinheiro" in formas_colunas
                        else -1
                    )

                    formas_style = TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONT", (0, 1), (-1, 1), "Helvetica", 8),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            # COR VERMELHA APENAS PARA OS VALORES DE SAÍDAS (linha 1)
                            (
                                (
                                    "TEXTCOLOR",
                                    (indice_saidas, 1),
                                    (indice_saidas, 1),
                                    colors.red,
                                )
                                if indice_saidas != -1
                                else ()
                            ),
                            # COR VERMELHA APENAS PARA OS VALORES DE ESTORNOS (linha 1)
                            (
                                (
                                    "TEXTCOLOR",
                                    (indice_estornos, 1),
                                    (indice_estornos, 1),
                                    colors.red,
                                )
                                if indice_estornos != -1
                                else ()
                            ),
                            (
                                (
                                    "TEXTCOLOR",
                                    (indice_total, 1),
                                    (indice_total, 1),
                                    colors.green,
                                )
                                if indice_total != -1
                                else ()
                            ),
                            # DESTACAR DINHEIRO MESMO QUE ZERO OU NEGATIVO
                            (
                                (
                                    "BACKGROUND",
                                    (indice_dinheiro, 0),
                                    (indice_dinheiro, 1),
                                    colors.lightblue,
                                )
                                if indice_dinheiro != -1
                                else ()
                            ),
                            (
                                (
                                    "FONT",
                                    (indice_dinheiro, 0),
                                    (indice_dinheiro, 1),
                                    "Helvetica-Bold",
                                    8,
                                )
                                if indice_dinheiro != -1
                                else ()
                            ),
                        ]
                    )
                    formas_table.setStyle(formas_style)
                    elements.append(Spacer(1, 6))
                    elements.append(formas_table)

                # OBSERVAÇÕES (com os valores que estavam nas colunas antigas)
                observacao_style = ParagraphStyle(
                    "Observacao",
                    parent=styles["Normal"],
                    fontSize=10,
                    textColor=colors.black,
                    leftIndent=0,
                )

                observacoes = []

                # Adicionar valores de abertura e fechamento
                if caixa.valor_abertura and caixa.valor_fechamento:
                    observacoes.append(
                        f"(Abertura) R$ {float(caixa.valor_abertura):,.2f} - (Fechamento) R$ {float(caixa.valor_fechamento):,.2f} = R$ {caixa.valor_abertura-caixa.valor_fechamento:,.2f}"
                    )

                observacoes.append(
                    f"Contas Recebidas: R$ {total_contas_recebidas:,.2f}"
                )

                # Juntar todas as observações em uma string
                texto_observacoes = " | ".join(observacoes)
                elements.append(Spacer(1, 4))
                elements.append(
                    Paragraph(f"Observações: {texto_observacoes}", observacao_style)
                )

                # NOVO: Armazenar totais por forma de pagamento para este caixa
                totais_formas_pagamento_por_caixa[caixa.id] = {
                    "operador": operador_nome,
                    "data_abertura": (
                        caixa.data_abertura.strftime("%d/%m/%Y")
                        if caixa.data_abertura
                        else "-"
                    ),
                    "formas_pagamento": todas_formas_pagamento.copy(),
                    "total_entradas": total_entradas_liquidas,
                    "total_saidas": total_saidas,
                    "saldo": saldo_caixa,
                }

                elements.append(Spacer(1, 12))

            # Verificação de consistência (para debug - pode ser removida em produção)
            diferenca = abs(soma_total_saidas_caixas - saldo_geral)
            if diferenca > 0.01:  # Tolerância de 1 centavo
                logging.warning(
                    f"Diferença encontrada na soma dos caixas: {diferenca:.2f}"
                )

            # NOVA SEÇÃO: Soma das Formas de Pagamento por Caixa
            elements.append(Spacer(1, 20))
            elements.append(
                Paragraph(
                    "🧮 Soma das Formas de Pagamento por Caixa", styles["Heading2"]
                )
            )
            elements.append(Spacer(1, 8))

            # Calcular totais consolidados das formas de pagamento dos caixas
            totais_consolidados_formas = {}

            for caixa_id, dados_caixa in totais_formas_pagamento_por_caixa.items():
                for forma, valor in dados_caixa["formas_pagamento"].items():
                    totais_consolidados_formas[forma] = (
                        totais_consolidados_formas.get(forma, 0) + valor
                    )

            # Ordenar formas de pagamento por valor (maior para menor)
            formas_ordenadas_consolidadas = [
                (f, totais_consolidados_formas.get(f, 0))
                for f in formas_prioridade_global
                if f in totais_consolidados_formas
            ]

            if formas_ordenadas_consolidadas:
                # Preparar dados para a tabela
                formas_colunas_consolidadas = []
                valores_colunas_consolidadas = []

                for forma, valor in formas_ordenadas_consolidadas:
                    if (
                        valor != 0
                    ):  # Mostrar apenas formas com valores diferentes de zero
                        forma_nome = forma.replace("_", " ").title()
                        formas_colunas_consolidadas.append(forma_nome)
                        valores_colunas_consolidadas.append(formatarMoeda(valor))

                # Adicionar linha de TOTAL
                formas_colunas_consolidadas.append("TOTAL GERAL")
                total_geral_formas = sum(
                    valor for _, valor in formas_ordenadas_consolidadas
                )
                valores_colunas_consolidadas.append(formatarMoeda(total_geral_formas))

                # Criar tabela
                formas_consolidadas_data = [
                    formas_colunas_consolidadas,
                    valores_colunas_consolidadas,
                ]

                # Calcular largura das colunas
                num_colunas_consolidadas = len(formas_colunas_consolidadas)
                if num_colunas_consolidadas > 0:
                    largura_coluna_consolidadas = 195 * mm / num_colunas_consolidadas

                    formas_consolidadas_table = Table(
                        formas_consolidadas_data,
                        colWidths=[largura_coluna_consolidadas]
                        * num_colunas_consolidadas,
                    )

                    formas_consolidadas_style = TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor("#32CD32"),
                            ),  # Verde mais escuro
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONT", (0, 1), (-1, 1), "Helvetica", 10),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            (
                                "BACKGROUND",
                                (-1, 0),
                                (-1, -1),
                                colors.HexColor("#228B22"),
                            ),  # Verde mais escuro para total
                            ("FONT", (-1, 0), (-1, -1), "Helvetica-Bold", 10),
                        ]
                    )
                    formas_consolidadas_table.setStyle(formas_consolidadas_style)
                    elements.append(formas_consolidadas_table)

                    # Adicionar observação explicativa
                    obs_style = ParagraphStyle(
                        "ObsConsolidado",
                        parent=styles["Normal"],
                        fontSize=8,
                        textColor=colors.grey,
                        alignment=TA_CENTER,
                    )
                    elements.append(Spacer(1, 6))
                    elements.append(
                        Paragraph(
                            "* Valores consolidados das formas de pagamento calculados a partir dos detalhes de cada caixa",
                            obs_style,
                        )
                    )

        else:
            # Mensagem quando não há caixas
            no_data_style = ParagraphStyle(
                "NoData",
                parent=styles["Normal"],
                fontSize=12,
                alignment=TA_CENTER,
                textColor=colors.gray,
            )
            elements.append(
                Paragraph(
                    "Nenhum caixa encontrado com os filtros aplicados.", no_data_style
                )
            )

        # -------------------- Rodapé --------------------
        elements.append(Spacer(1, 15))
        rodape = datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M")
        elements.append(
            Paragraph(
                rodape,
                ParagraphStyle(
                    "Rodape", fontSize=8, alignment=TA_RIGHT, textColor=colors.grey
                ),
            )
        )

        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            "inline; filename=relatorio_caixas.pdf"
        )
        return response

    except Exception as e:
        logging.error(f"Erro ao gerar PDF dos caixas: {str(e)}", exc_info=True)
        session.rollback()
        return (
            jsonify({"success": False, "error": f"Erro interno do servidor: {str(e)}"}),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/caixas/<int:caixa_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_caixa_route(caixa_id):
    try:
        dados = request.get_json()
        if not dados:
            logger.warning("Dados não fornecidos para atualização do caixa")
            return jsonify({"success": False, "error": "Dados não fornecidos"}), 400

        caixa = db.session.get(Caixa, caixa_id)
        if not caixa:
            logger.warning(f"Caixa não encontrado: ID {caixa_id}")
            return jsonify({"success": False, "error": "Caixa não encontrado"}), 404

        # Atualiza status e datas conforme ação
        if "status" in dados:
            if dados["status"] == "fechado":
                caixa.status = StatusCaixa.fechado
                caixa.data_fechamento = datetime.now()
            elif dados["status"] == "analise":
                caixa.status = StatusCaixa.analise
                caixa.data_analise = datetime.now()

        if "valor_fechamento" in dados:
            caixa.valor_fechamento = Decimal(dados["valor_fechamento"])
        if "valor_abertura" in dados:
            caixa.valor_abertura = Decimal(dados["valor_abertura"])

        # Atualiza observações se existirem
        if "observacoes_admin" in dados:
            caixa.observacoes_admin = dados["observacoes_admin"]

        db.session.commit()
        logger.info(f"Caixa atualizado com sucesso: ID {caixa_id}")
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Caixa atualizado com sucesso",
                    "caixa": {
                        "id": caixa.id,
                        "status": caixa.status.value,
                        "data_analise": (
                            caixa.data_analise.isoformat()
                            if caixa.data_analise
                            else None
                        ),
                        "data_fechamento": (
                            caixa.data_fechamento.isoformat()
                            if caixa.data_fechamento
                            else None
                        ),
                        "observacoes_admin": caixa.observacoes_admin,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Erro ao atualizar caixa ID {caixa_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"success": False, "error": "Erro ao atualizar caixa: "}), 500


@admin_bp.route("/caixas/<int:caixa_id>", methods=["GET", "PUT"])
@login_required
@admin_required
def caixa_detail(caixa_id):
    if request.method == "GET":
        try:
            session = Session(db.engine)
            caixa = session.get(Caixa, caixa_id)

            if not caixa:
                logger.warning(f"Caixa não encontrado: ID {caixa_id}")
                return jsonify({"success": False, "error": "Caixa não encontrado"}), 404

            # Convert caixa object to dictionary
            caixa_data = {
                "id": caixa.id,
                "operador": {
                    "id": caixa.operador.id,
                    "nome": caixa.operador.nome,
                    "tipo": caixa.operador.tipo,
                },
                "data_abertura": caixa.data_abertura.isoformat(),
                "data_fechamento": (
                    caixa.data_fechamento.isoformat() if caixa.data_fechamento else None
                ),
                "valor_abertura": float(caixa.valor_abertura),
                "valor_fechamento": (
                    float(caixa.valor_fechamento) if caixa.valor_fechamento else None
                ),
                "status": caixa.status.value,
                "observacoes_operador": caixa.observacoes_operador,
                "observacoes_admin": caixa.observacoes_admin,
            }
            logger.info(f"Caixa recuperado com sucesso: ID {caixa_id}")
            return jsonify({"success": True, "data": caixa_data})

        except Exception as e:
            logger.error(
                f"Erro ao recuperar caixa ID {caixa_id}: {str(e)}", exc_info=True
            )
            return (
                jsonify({"success": False, "error": "Erro ao recuperar caixa: "}),
                500,
            )

    elif request.method == "PUT":
        try:
            dados = request.get_json()
            if not dados:
                logger.warning("Dados não fornecidos para atualização do caixa")
                return jsonify({"success": False, "error": "Dados não fornecidos"}), 400

            caixa = db.session.get(Caixa, caixa_id)
            if not caixa:
                logger.warning(f"Caixa não encontrado: ID {caixa_id}")
                return jsonify({"success": False, "error": "Caixa não encontrado"}), 404

            # Atualiza status e datas conforme ação
            if "status" in dados:
                if dados["status"] == "fechado" and caixa.status != StatusCaixa.fechado:
                    caixa.status = StatusCaixa.fechado
                    caixa.data_fechamento = datetime.now()
                elif (
                    dados["status"] == "analise" and caixa.status != StatusCaixa.analise
                ):
                    caixa.status = StatusCaixa.analise
                    caixa.data_analise = datetime.now()

            # Atualiza observações se existirem
            if "observacoes_operador" in dados:
                caixa.observacoes_operador = dados["observacoes_operador"]
            if "observacoes_admin" in dados:
                caixa.observacoes_admin = dados["observacoes_admin"]

            db.session.commit()
            logger.info(
                f"Caixa atualizado com sucesso: ID {caixa_id} por usuário {current_user.nome}"
            )
            return jsonify(
                {
                    "success": True,
                    "message": "Caixa atualizado com sucesso",
                    "data": {
                        "id": caixa.id,
                        "status": caixa.status.value,
                        "data_analise": (
                            caixa.data_analise.isoformat()
                            if caixa.data_analise
                            else None
                        ),
                        "data_fechamento": (
                            caixa.data_fechamento.isoformat()
                            if caixa.data_fechamento
                            else None
                        ),
                    },
                }
            )

        except Exception as e:
            logger.error(
                f"Erro ao atualizar caixa ID {caixa_id}: {str(e)}", exc_info=True
            )
            db.session.rollback()
            return (
                jsonify({"success": False, "error": "Erro ao atualizar caixa: "}),
                500,
            )


@admin_bp.route("/caixa/venda/<int:venda_id>/estornar", methods=["POST"])
@login_required
@admin_required
def rota_estornar_venda(venda_id):
    """
    Rota para estornar uma venda
    """
    try:
        dados = request.get_json()

        if not dados:
            logger.warning("Dados não fornecidos para estorno de venda")
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400

        motivo_estorno = dados.get("motivo_estorno")
        if not motivo_estorno:
            logger.warning("Motivo do estorno não fornecido")
            return (
                jsonify(
                    {"success": False, "message": "Motivo do estorno é obrigatório"}
                ),
                400,
            )

        usuario_id = current_user.id

        resultado = estornar_venda(db, venda_id, motivo_estorno, usuario_id)

        logger.info(f"Estorno de venda ID {venda_id} processado: {resultado}")
        return jsonify(resultado), 200 if resultado["success"] else 400

    except Exception as e:
        logger.error(f"Erro ao estornar venda ID {venda_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return (
            jsonify({"success": False, "message": "Erro interno ao processar estorno"}),
            500,
        )


@admin_bp.route("/caixas/<int:caixa_id>/financeiro")
@login_required
@admin_required
def get_caixa_financeiro(caixa_id):
    session = Session(db.engine)
    try:
        # Busca informações do caixa
        caixa = session.query(Caixa).filter_by(id=caixa_id).first()
        if not caixa:
            logger.warning(f"Caixa não encontrado: ID {caixa_id}")
            return jsonify({"success": False, "error": "Caixa não encontrado"}), 404

        # Busca todas as movimentações financeiras do caixa
        movimentacoes = (
            session.query(Financeiro)
            .filter_by(caixa_id=caixa_id)
            .order_by(Financeiro.data.desc())
            .all()
        )

        # Inicializa estrutura de dados das movimentações
        dados = []
        for mov in movimentacoes:
            # Busca informações do cliente
            cliente_nome = None
            if mov.cliente_id:
                cliente = session.query(Cliente).get(mov.cliente_id)
                cliente_nome = cliente.nome if cliente else None

            # Busca formas de pagamento
            formas_pagamento = []
            if mov.nota_fiscal_id:
                pagamentos = (
                    session.query(PagamentoNotaFiscal)
                    .filter_by(nota_fiscal_id=mov.nota_fiscal_id)
                    .all()
                )
                formas_pagamento = [p.forma_pagamento.value for p in pagamentos]

            if mov.conta_receber_id:
                pagamentos = (
                    session.query(PagamentoContaReceber)
                    .filter_by(conta_id=mov.conta_receber_id)
                    .all()
                )
                formas_pagamento = [p.forma_pagamento.value for p in pagamentos]

            dados.append(
                {
                    "id": mov.id,
                    "data": mov.data.isoformat(),
                    "tipo": mov.tipo.value,
                    "categoria": mov.categoria.value if mov.categoria else None,
                    "valor": float(mov.valor),
                    "descricao": mov.descricao,
                    "nota_fiscal_id": mov.nota_fiscal_id,
                    "cliente_id": mov.cliente_id,
                    "conta_receber_id": mov.conta_receber_id,
                    "cliente_nome": cliente_nome,
                    "formas_pagamento": formas_pagamento,
                }
            )

        # ---- Usa a função nova para calcular os totais ----
        totais = calcular_formas_pagamento(caixa_id, session)

        logger.info(f"Dados financeiros do caixa ID {caixa_id} recuperados com sucesso")
        return jsonify(
            {
                "success": True,
                "data": dados,
                "totais": {
                    "entradas": totais["entradas"],
                    "saidas": totais["saidas"],
                    "saldo": totais["saldo"],
                    "valor_fisico": totais["valor_fisico"],
                    "valor_digital": totais["valor_digital"],
                    "a_prazo": totais["a_prazo"],
                    "contas_prazo_recebidas": totais["contas_prazo_recebidas"],
                },
                "vendas_por_forma_pagamento": totais["vendas_por_forma_pagamento"],
            }
        )

    except Exception as e:
        logger.error(f"Erro no financeiro do caixa {caixa_id}: {str(e)}", exc_info=True)
        session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro interno ao processar dados financeiros",
                }
            ),
            500,
        )
    finally:
        session.close()


@admin_bp.route("/caixas/<int:caixa_id>/financeiro/movimentacoes/pdf")
@login_required
@admin_required
def get_caixa_financeiro_pdf(caixa_id):
    session = Session(db.engine)
    try:
        # Busca informações do caixa
        caixa = session.query(Caixa).filter_by(id=caixa_id).first()
        if not caixa:
            logger.warning(f"Caixa não encontrado: ID {caixa_id}")
            return jsonify({"success": False, "error": "Caixa não encontrado"}), 404

        # Busca todas as movimentações financeiras do caixa
        movimentacoes = (
            session.query(Financeiro)
            .filter_by(caixa_id=caixa_id)
            .order_by(Financeiro.data.desc())
            .all()
        )

        # Busca informações adicionais para o PDF
        operador_nome = caixa.operador.nome if caixa.operador else "Desconhecido"
        data_abertura = (
            caixa.data_abertura.strftime("%d/%m/%Y %H:%M")
            if caixa.data_abertura
            else "N/A"
        )
        data_fechamento = (
            caixa.data_fechamento.strftime("%d/%m/%Y %H:%M")
            if caixa.data_fechamento
            else "N/A"
        )

        # Prepara dados para o PDF
        pdf_data = {
            "caixa_id": caixa_id,
            "operador": operador_nome,
            "data_abertura": data_abertura,
            "data_fechamento": data_fechamento,
            "status": caixa.status.value,
            "movimentacoes": [],
        }

        # Dicionário para agrupar movimentações por nota fiscal
        notas_processadas = set()

        for mov in movimentacoes:
            # Pula movimentações de notas fiscais já processadas
            if mov.nota_fiscal_id and mov.nota_fiscal_id in notas_processadas:
                continue

            # Busca informações do cliente
            cliente_nome = None
            if mov.cliente_id:
                cliente = session.query(Cliente).get(mov.cliente_id)
                cliente_nome = cliente.nome if cliente else None

            # Busca formas de pagamento detalhadas
            formas_pagamento_detalhadas = []
            valor_total = float(mov.valor)  # Valor padrão é o da movimentação

            # Para notas fiscais, busca a nota completa e todos os pagamentos
            if mov.nota_fiscal_id:
                notas_processadas.add(mov.nota_fiscal_id)

                # Busca a nota fiscal para obter o valor total
                nota_fiscal = session.query(NotaFiscal).get(mov.nota_fiscal_id)
                if nota_fiscal:
                    valor_total = float(nota_fiscal.valor_total)

                # Busca todos os pagamentos da nota
                pagamentos = (
                    session.query(PagamentoNotaFiscal)
                    .filter_by(nota_fiscal_id=mov.nota_fiscal_id)
                    .all()
                )
                for p in pagamentos:
                    formas_pagamento_detalhadas.append(
                        {"forma": p.forma_pagamento.value, "valor": float(p.valor)}
                    )

            # Para contas a receber, busca todos os pagamentos da conta
            elif mov.conta_receber_id:
                # Busca a conta para obter o valor original
                conta = session.query(ContaReceber).get(mov.conta_receber_id)
                if conta:
                    valor_total = float(conta.valor_original)

                pagamentos = (
                    session.query(PagamentoContaReceber)
                    .filter_by(conta_id=mov.conta_receber_id)
                    .all()
                )
                for p in pagamentos:
                    formas_pagamento_detalhadas.append(
                        {"forma": p.forma_pagamento.value, "valor": float(p.valor_pago)}
                    )

            # Para outras movimentações, usa o valor da própria movimentação
            else:
                formas_pagamento_detalhadas.append(
                    {"forma": "N/A", "valor": float(mov.valor)}
                )

            pdf_data["movimentacoes"].append(
                {
                    "data": mov.data.strftime("%d/%m/%Y %H:%M"),
                    "tipo": mov.tipo.value,
                    "categoria": mov.categoria.value if mov.categoria else "N/A",
                    "valor": valor_total,  # Usa o valor total da nota/conta
                    "descricao": mov.descricao or "N/A",
                    "cliente_nome": cliente_nome,
                    "formas_pagamento": formas_pagamento_detalhadas,
                    "nota_fiscal_id": mov.nota_fiscal_id,
                }
            )

        # Gera o PDF
        pdf_content = generate_caixa_financeiro_pdf(pdf_data)

        return Response(
            pdf_content,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=caixa_{caixa_id}_financeiro.pdf"
            },
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF do caixa {caixa_id}: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({"success": False, "error": "Erro interno ao gerar PDF"}), 500
    finally:
        session.close()


@admin_bp.route("/vendas/<int:venda_id>/atualizar-pagamentos", methods=["POST"])
@login_required
@admin_required
def atualizar_forma_pagamentos(venda_id):
    """
    Atualiza TODOS os pagamentos associados à nota fiscal e registros relacionados
    para as formas de pagamento recebidas no JSON.
    Recebe JSON com {"pagamentos": [{"forma_pagamento": "PIX", "valor": 100.00}, ...]}.
    """
    data = request.get_json()
    pagamentos_recebidos = data.get("pagamentos")

    if not pagamentos_recebidos or not isinstance(pagamentos_recebidos, list):
        logger.warning("Lista de pagamentos inválida ou não fornecida")
        return (
            jsonify({"success": False, "error": "Informe a lista de pagamentos"}),
            400,
        )

    for i, pagamento in enumerate(pagamentos_recebidos):
        if not pagamento.get("forma_pagamento"):
            logger.warning(f"Forma de pagamento inválida no item {i}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Forma de pagamento inválida no item {i}",
                    }
                ),
                400,
            )
        if "valor" not in pagamento:
            logger.warning(f"Valor não informado no item {i}")
            return (
                jsonify(
                    {"success": False, "error": f"Valor não informado no item {i}"}
                ),
                400,
            )

    session: Session = db.session
    try:
        nota_fiscal = session.query(NotaFiscal).get(venda_id)
        if not nota_fiscal:
            logger.warning(f"Nota fiscal não encontrada: ID {venda_id}")
            return (
                jsonify({"success": False, "error": "Nota fiscal não encontrada"}),
                404,
            )

        caixa_aberto = get_caixa_aberto(session, operador_id=nota_fiscal.operador_id)
        if not caixa_aberto:
            logger.warning(f"Caixa não encontrado para a nota fiscal {venda_id}")
            return (
                jsonify({"success": False, "error": "Caixa não encontrado"}),
                404,
            )

        pagamentos_existentes = (
            session.query(PagamentoNotaFiscal).filter_by(nota_fiscal_id=venda_id).all()
        )

        pagamento_ids = [p.id for p in pagamentos_existentes]

        if pagamento_ids:
            session.query(Financeiro).filter(
                Financeiro.pagamento_id.in_(pagamento_ids)
            ).delete(synchronize_session=False)

        session.query(PagamentoNotaFiscal).filter_by(nota_fiscal_id=venda_id).delete(
            synchronize_session=False
        )

        conta_receber_existente = (
            session.query(ContaReceber).filter_by(nota_fiscal_id=venda_id).first()
        )

        if conta_receber_existente:
            session.delete(conta_receber_existente)

        pagamentos_ids = []
        valor_a_prazo = Decimal(0)
        valor_total_pagamentos = Decimal(0)

        for pagamento_data in pagamentos_recebidos:
            forma = pagamento_data.get("forma_pagamento")
            valor = Decimal(str(pagamento_data.get("valor")))

            try:
                forma_enum = FormaPagamento(forma)
            except ValueError:
                forma_enum = forma

            pagamento_nf = PagamentoNotaFiscal(
                nota_fiscal_id=nota_fiscal.id,
                forma_pagamento=forma_enum,
                valor=valor,
                data=datetime.now(),
                sincronizado=False,
            )
            session.add(pagamento_nf)
            session.flush()

            pagamentos_ids.append(pagamento_nf.id)
            valor_total_pagamentos += valor

            if forma != "a_prazo":
                financeiro = Financeiro(
                    tipo=TipoMovimentacao.entrada,
                    categoria=CategoriaFinanceira.venda,
                    valor=valor,
                    descricao=f"Pagamento venda NF #{nota_fiscal.id} (editado por {current_user.nome})",
                    cliente_id=nota_fiscal.cliente_id,
                    caixa_id=nota_fiscal.caixa_id,
                    nota_fiscal_id=nota_fiscal.id,
                    pagamento_id=pagamento_nf.id,
                    sincronizado=False,
                )
                session.add(financeiro)
            else:
                valor_a_prazo += valor

        diferenca = abs(valor_total_pagamentos - nota_fiscal.valor_total)
        if diferenca > Decimal("0.01"):
            logger.warning(
                f"Soma dos novos pagamentos ({valor_total_pagamentos}) não confere com valor total da nota ({nota_fiscal.valor_total})"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Soma dos pagamentos ({valor_total_pagamentos}) não confere com valor total da venda ({nota_fiscal.valor_total})",
                    }
                ),
                400,
            )

        if valor_a_prazo > 0:
            conta_receber = ContaReceber(
                cliente_id=nota_fiscal.cliente_id,
                nota_fiscal_id=nota_fiscal.id,
                descricao=f"Venda a prazo NF #{nota_fiscal.id} (editado por {current_user.nome})",
                valor_original=valor_a_prazo,
                valor_aberto=valor_a_prazo,
                data_vencimento=datetime.now() + timedelta(days=30),
                status=StatusPagamento.pendente,
                sincronizado=False,
            )
            session.add(conta_receber)

        if len(pagamentos_recebidos) == 1:
            nota_fiscal.forma_pagamento = FormaPagamento(
                pagamentos_recebidos[0]["forma_pagamento"]
            )
        else:
            nota_fiscal.forma_pagamento = FormaPagamento.dinheiro

        nota_fiscal.a_prazo = valor_a_prazo > 0

        valor_recebido = valor_total_pagamentos - valor_a_prazo
        nota_fiscal.valor_recebido = valor_recebido
        nota_fiscal.troco = max(valor_recebido - nota_fiscal.valor_total, Decimal(0))

        movimentacoes = (
            session.query(MovimentacaoEstoque)
            .filter_by(caixa_id=nota_fiscal.caixa_id, tipo=TipoMovimentacao.saida)
            .all()
        )

        if len(pagamentos_recebidos) == 1:
            nova_forma_enum = FormaPagamento(pagamentos_recebidos[0]["forma_pagamento"])
            for mov in movimentacoes:
                mov.forma_pagamento = nova_forma_enum

        session.commit()

        logger.info(
            f"Formas de pagamento da venda {venda_id} atualizadas. "
            f"Total de {len(pagamentos_recebidos)} pagamentos registrados. "
            f"Valor a prazo: {valor_a_prazo}"
        )

        return jsonify(
            {
                "success": True,
                "mensagem": "Formas de pagamento atualizadas com sucesso!",
                "pagamentos_ids": pagamentos_ids,
                "valor_a_prazo": float(valor_a_prazo) if valor_a_prazo > 0 else 0,
                "valor_recebido": float(valor_recebido),
                "troco": float(nota_fiscal.troco) if nota_fiscal.troco else 0,
            }
        )

    except Exception as e:
        session.rollback()
        import logging

        logging.exception(f"Erro ao atualizar pagamentos da venda {venda_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Erro interno ao atualizar pagamentos: {str(e)}",
                }
            ),
            500,
        )


@admin_bp.route("/caixas/<int:caixa_id>/vendas-por-pagamento")
@login_required
@admin_required
def get_vendas_por_pagamento(caixa_id):
    session = Session(db.engine)
    try:
        forma_pagamento = request.args.get("forma_pagamento")
        if not forma_pagamento:
            logger.warning("Forma de pagamento não especificada")
            return (
                jsonify(
                    {"success": False, "error": "Forma de pagamento não especificada"}
                ),
                400,
            )

        vendas = (
            session.query(NotaFiscal)
            .join(PagamentoNotaFiscal)
            .filter(
                NotaFiscal.caixa_id == caixa_id,
                NotaFiscal.status == StatusNota.emitida,
                PagamentoNotaFiscal.forma_pagamento == forma_pagamento,
            )
            .all()
        )

        vendas_data = []
        for venda in vendas:
            valor_pago = (
                session.query(func.sum(PagamentoNotaFiscal.valor))
                .filter(
                    PagamentoNotaFiscal.nota_fiscal_id == venda.id,
                    PagamentoNotaFiscal.forma_pagamento == forma_pagamento,
                )
                .scalar()
                or 0.0
            )

            vendas_data.append(
                {
                    "id": venda.id,
                    "data_emissao": venda.data_emissao.isoformat(),
                    "cliente_nome": venda.cliente.nome if venda.cliente else None,
                    "valor_total": float(venda.valor_total),
                    "valor_pago": float(valor_pago),
                }
            )
        logger.info(
            f"Vendas por pagamento '{forma_pagamento}' no caixa {caixa_id} recuperadas com sucesso"
        )
        return jsonify(
            {"success": True, "vendas": vendas_data, "forma_pagamento": forma_pagamento}
        )

    except Exception as e:
        logger.error(f"Erro ao buscar vendas por pagamento: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({"success": False, "error": "Erro interno"}), 500
    finally:
        session.close()


@admin_bp.route("/caixas/<int:caixa_id>/contas-prazo-recebidas")
@login_required
@admin_required
def get_contas_prazo_recebidas(caixa_id):
    session = Session(db.engine)
    try:
        pagamentos = (
            session.query(PagamentoContaReceber)
            .join(ContaReceber)
            .filter(PagamentoContaReceber.caixa_id == caixa_id)
            .all()
        )

        pagamentos_data = []
        for p in pagamentos:
            pagamentos_data.append({
                "id": p.id,
                "conta_id": p.conta_id,
                "nota_fiscal_id": p.conta.nota_fiscal_id,
                "data_pagamento": p.data_pagamento.isoformat(),
                "cliente_nome": p.conta.cliente.nome if p.conta.cliente else "N/A",
                "valor_pago": float(p.valor_pago),
                "forma_pagamento": p.forma_pagamento.value,
                "descricao": p.conta.descricao
            })

        return jsonify({"success": True, "pagamentos": pagamentos_data})
    except Exception as e:
        logger.error(f"Erro ao buscar pagamentos de contas a prazo: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno"}), 500
    finally:
        session.close()

@admin_bp.route("/caixas/<int:caixa_id>/vendas-por-pagamento/pdf")
@login_required
@admin_required
def get_vendas_por_pagamento_pdf(caixa_id):
    session = Session(db.engine)
    try:
        forma_pagamento = request.args.get("forma_pagamento")
        if not forma_pagamento:
            logger.warning("Forma de pagamento não especificada para PDF")
            return (
                jsonify(
                    {"success": False, "error": "Forma de pagamento não especificada"}
                ),
                400,
            )

        # Busca vendas
        vendas = (
            session.query(NotaFiscal)
            .join(PagamentoNotaFiscal)
            .filter(
                NotaFiscal.caixa_id == caixa_id,
                NotaFiscal.status == StatusNota.emitida,
                PagamentoNotaFiscal.forma_pagamento == forma_pagamento,
            )
            .all()
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )
        styles = getSampleStyleSheet()
        elements = []

        # Título
        elements.append(
            Paragraph(f"Relatório de Vendas - {forma_pagamento}", styles["Title"])
        )
        elements.append(Spacer(1, 12))

        # Verifica se alguma venda teve desconto
        tem_desconto = any(float(venda.valor_desconto or 0) > 0 for venda in vendas)

        # Cabeçalho da tabela - adiciona coluna de desconto somente se houver desconto
        cabecalho = ["Data", "Nota Fiscal", "Cliente", "Valor Total"]
        if tem_desconto:
            cabecalho.append("Desconto")
        cabecalho.append("Valor Pago")

        data = [cabecalho]

        # Variáveis para calcular totais
        total_valor_total = 0.0
        total_valor_desconto = 0.0
        total_valor_pago = 0.0

        # Preencher linhas
        for venda in vendas:
            valor_pago = (
                session.query(func.sum(PagamentoNotaFiscal.valor))
                .filter(
                    PagamentoNotaFiscal.nota_fiscal_id == venda.id,
                    PagamentoNotaFiscal.forma_pagamento == forma_pagamento,
                )
                .scalar()
                or 0.0
            )

            # Adiciona aos totais
            total_valor_total += float(venda.valor_total)
            total_valor_desconto += float(venda.valor_desconto or 0)
            total_valor_pago += float(valor_pago)

            # Prepara a linha da venda
            linha = [
                venda.data_emissao.strftime("%d/%m/%Y %H:%M"),
                str(venda.id),
                venda.cliente.nome if venda.cliente else "Não informado",
                f"R$ {venda.valor_total:,.2f}",
            ]

            # Adiciona coluna de desconto somente se houver desconto
            if tem_desconto:
                linha.append(
                    f"R$ {venda.valor_desconto:,.2f}"
                    if float(venda.valor_desconto or 0) > 0
                    else "R$ 0,00"
                )

            linha.append(f"R$ {valor_pago:,.2f}")

            data.append(linha)

        # Adicionar linha de totais
        linha_total = ["", "", "TOTAL:", f"R$ {total_valor_total:,.2f}"]

        if tem_desconto:
            linha_total.append(f"R$ {total_valor_desconto:,.2f}")

        linha_total.append(f"R$ {total_valor_pago:,.2f}")
        data.append(linha_total)

        # Criar tabela
        table = Table(data, repeatRows=1)

        # Estilo da tabela
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e6e6e6")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 11),
        ]

        # Se houver desconto, destaca as células com desconto > 0
        if tem_desconto:
            for i, venda in enumerate(
                vendas, start=1
            ):  # start=1 para pular o cabeçalho
                if float(venda.valor_desconto or 0) > 0:
                    # Destaca a célula de desconto (coluna 4, considerando 0-based index)
                    estilo.append(("BACKGROUND", (4, i), (4, i), colors.yellow))
                    estilo.append(("TEXTCOLOR", (4, i), (4, i), colors.red))

        table.setStyle(TableStyle(estilo))
        elements.append(table)

        # Montar PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f"inline; filename=vendas_{forma_pagamento}.pdf"
        )
        return response

    except Exception as e:
        logger.error(f"Erro ao gerar PDF de vendas: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({"success": False, "error": "Erro interno ao gerar PDF"}), 500
    finally:
        session.close()


@admin_bp.route("/vendas/<int:venda_id>/detalhes")
@login_required
@admin_required
def get_detalhes_venda(venda_id):
    session = Session(db.engine)
    try:
        venda = (
            session.query(NotaFiscal)
            .options(
                joinedload(NotaFiscal.cliente),
                joinedload(NotaFiscal.itens).joinedload(NotaFiscalItem.produto),
                joinedload(NotaFiscal.pagamentos),
            )
            .filter(NotaFiscal.id == venda_id)
            .first()
        )

        if not venda:
            logger.warning(f"Venda não encontrada: ID {venda_id}")
            return jsonify({"success": False, "error": "Venda não encontrada"}), 404

        venda_data = {
            "id": venda.id,
            "data_emissao": venda.data_emissao.isoformat(),
            "cliente_nome": venda.cliente.nome if venda.cliente else None,
            "valor_total": float(venda.valor_total),
            "valor_desconto": (
                float(venda.valor_desconto) if venda.valor_desconto else 0.0
            ),
            "tipo_desconto": venda.tipo_desconto.value if venda.tipo_desconto else None,
            "pagamentos": [],
            "itens": [],
        }

        # Formas de pagamento
        for pagamento in venda.pagamentos:
            venda_data["pagamentos"].append(
                {
                    "forma_pagamento": pagamento.forma_pagamento.value,
                    "valor": float(pagamento.valor),
                }
            )

        # Itens da venda
        for item in venda.itens:
            venda_data["itens"].append(
                {
                    "produto_nome": item.produto.nome,
                    "quantidade": float(item.quantidade),
                    "unidade_medida": item.produto.unidade.value,
                    "valor_unitario": float(item.valor_unitario),
                    "valor_total": float(item.valor_total),
                    "desconto_aplicado": (
                        float(item.desconto_aplicado)
                        if item.desconto_aplicado
                        else None
                    ),
                    "tipo_desconto": (
                        item.tipo_desconto.value if item.tipo_desconto else None
                    ),
                }
            )
        logger.info(f"Detalhes da venda ID {venda_id} recuperados com sucesso")
        return jsonify({"success": True, "venda": venda_data})

    except Exception as e:
        logger.error(
            f"Erro ao buscar detalhes da venda {venda_id}: {str(e)}", exc_info=True
        )
        session.rollback()
        return jsonify({"success": False, "error": "Erro interno"}), 500
    finally:
        session.close()


@admin_bp.route("/caixas/<int:caixa_id>/financeiro/pdf")
@login_required
@admin_required
def gerar_pdf_caixa_financeiro(caixa_id):
    session = Session(db.engine)
    try:
        # --- Busca informações do caixa e operador ---
        caixa = session.query(Caixa).filter_by(id=caixa_id).first()
        if not caixa:
            logger.warning(f"Caixa não encontrado para PDF: ID {caixa_id}")
            raise Exception("Caixa não encontrado")
        operador_nome = (
            caixa.operador.nome if caixa.operador else "Operador não identificado"
        )
        caixa_data = (
            caixa.data_fechamento if caixa.data_fechamento else caixa.data_abertura
        )

        # --- BUSCA EXATAMENTE COMO NA API ---
        # Busca todas as movimentações financeiras do caixa
        movimentacoes = (
            session.query(Financeiro)
            .filter_by(caixa_id=caixa_id)
            .order_by(Financeiro.data.desc())
            .all()
        )

        # --- CALCULA TOTAIS EXATAMENTE COMO NA API ---
        # 1. CALCULA TOTAL DE ENTRADAS - SOMA TODAS AS FORMAS DE PAGAMENTO
        # Busca pagamentos de notas fiscais (MESMO QUE NA API)
        pagamentos_notas = (
            session.query(
                PagamentoNotaFiscal.forma_pagamento,
                func.sum(PagamentoNotaFiscal.valor).label("total"),
            )
            .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
            .filter(
                NotaFiscal.caixa_id == caixa_id, NotaFiscal.status == StatusNota.emitida
            )
            .group_by(PagamentoNotaFiscal.forma_pagamento)
            .all()
        )

        # Busca pagamentos de contas a receber (MESMO QUE NA API)
        pagamentos_contas = (
            session.query(
                PagamentoContaReceber.forma_pagamento,
                func.sum(PagamentoContaReceber.valor_pago).label("total"),
            )
            .filter(PagamentoContaReceber.caixa_id == caixa_id)
            .group_by(PagamentoContaReceber.forma_pagamento)
            .all()
        )

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
        total_saidas = (
            session.query(func.sum(Financeiro.valor))
            .filter(
                Financeiro.caixa_id == caixa_id,
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria == CategoriaFinanceira.despesa,
            )
            .scalar()
            or 0.0
        )

        total_saidas = float(total_saidas)

        # 3. CALCULA VALORES FÍSICOS E DIGITAIS (MESMO QUE NA API)
        valor_dinheiro = formas_pagamento.get("dinheiro", 0.0)
        valor_fisico = valor_dinheiro

        if caixa.valor_fechamento and caixa.valor_abertura:
            valor_abertura = float(caixa.valor_abertura)
            valor_fechamento = float(caixa.valor_fechamento)
            valor_fisico = max(
                (valor_dinheiro + valor_abertura) - valor_fechamento - total_saidas, 0.0
            )

            # Pega parte inteira e parte decimal (MESMO QUE NA API)
            parte_inteira = math.floor(valor_fisico)
            parte_decimal = valor_fisico - parte_inteira

            # if parte_decimal == 0.5:
            #     # Mantém o valor original (sem arredondar)
            #     valor_fisico = valor_fisico
            # elif parte_decimal > 0.5:
            #     valor_fisico = math.ceil(valor_fisico)  # mais perto do de cima
            # else:
            #     valor_fisico = math.floor(valor_fisico)  # mais perto do de baixo

        formas_pagamento["dinheiro"] = valor_fisico
        valor_digital = sum(
            [
                formas_pagamento.get("pix_loja", 0.0),
                formas_pagamento.get("pix_fabiano", 0.0),
                formas_pagamento.get("pix_edfrance", 0.0),
                formas_pagamento.get("pix_maquineta", 0.0),
                formas_pagamento.get("cartao_debito", 0.0),
                formas_pagamento.get("cartao_credito", 0.0),
            ]
        )

        a_prazo = formas_pagamento.get("a_prazo", 0.0)

        # 4. CALCULA TOTAL RECEBIDO DE CONTAS A PRAZO (MESMO QUE NA API)
        total_contas_prazo_recebidas = (
            session.query(func.sum(PagamentoContaReceber.valor_pago))
            .filter(PagamentoContaReceber.caixa_id == caixa_id)
            .scalar()
            or 0.0
        )

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
            bottomMargin=5,
        )
        elements = []

        # --- Estilos ---
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            name="Header",
            parent=styles["Heading1"],
            fontSize=14,
            leading=14,
            alignment=1,
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            name="Subtitle",
            parent=styles["Heading2"],
            fontSize=12,
            leading=12,
            alignment=1,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        normal_style = ParagraphStyle(
            name="Normal",
            parent=styles["Normal"],
            fontSize=10,
            leading=10,
            alignment=0,
            fontName="Helvetica",
        )
        valor_style = ParagraphStyle(
            name="Valor", parent=normal_style, alignment=2, fontName="Helvetica-Bold"
        )
        linha_style = ParagraphStyle(
            name="Linha", parent=normal_style, alignment=1, textColor=colors.black
        )

        def moeda_br(valor):
            return (
                f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        def linha_separadora():
            return Paragraph("=" * 34, linha_style)

        # Função para criar linha alinhada com tabela invisível
        from reportlab.platypus import Table, TableStyle

        def linha_dupla(label, valor):
            tabela = Table(
                [[Paragraph(label, normal_style), Paragraph(valor, valor_style)]],
                colWidths=[120, 80],
            )
            tabela.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            return tabela

        # --- Logo ---
        from flask import current_app
        import os
        from PIL import Image as PILImage
        from reportlab.platypus import Image, Spacer

        logo_path = os.path.join(current_app.root_path, "static", "assets", "logo.jpeg")
        if os.path.exists(logo_path):
            try:
                with PILImage.open(logo_path) as img:
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                logo_width = 250
                logo_height = logo_width / aspect_ratio
                logo = Image(logo_path, width=logo_width, height=logo_height)
                logo.hAlign = "CENTER"
                elements.append(logo)
                elements.append(Spacer(0, 6))
            except Exception as e:
                logger.error(f"Erro ao carregar a logo: {e}")
                logger.warning(f"Erro ao carregar a logo: {e}")

        # --- Cabeçalho ---
        elements.append(Paragraph("RELATÓRIO FINANCEIRO", header_style))
        elements.append(linha_separadora())
        elements.append(Spacer(1, 6))
        data_relatorio = (
            caixa_data.strftime("%d/%m/%Y %H:%M")
            if caixa_data
            else "Data não disponível"
        )
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
        elements.append(
            linha_dupla("A Prazo Recebidos:", moeda_br(total_contas_prazo_recebidas))
        )

        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())
        elements.append(Spacer(1, 1))
        elements.append(Paragraph("Valores do Caixa", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(linha_separadora())

        # Adiciona valores de abertura e fechamento apenas se existirem
        valor_abertura = float(caixa.valor_abertura) if caixa.valor_abertura else 0.0
        valor_fechamento = (
            float(caixa.valor_fechamento) if caixa.valor_fechamento else 0.0
        )

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
            "dinheiro": "Dinheiro",
            "pix_loja": "PIX Loja",
            "pix_fabiano": "PIX Fabiano",
            "pix_edfrance": "PIX Edfranci",
            "pix_maquineta": "PIX Maquineta",
            "cartao_debito": "Cartão Débito",
            "cartao_credito": "Cartão Crédito",
            "a_prazo": "A Prazo",
        }

        # Exibe todas as formas de pagamento que têm valor
        for forma, valor in formas_pagamento.items():
            if valor > 0:
                nome_forma = nomes_formas.get(forma, forma)
                elements.append(linha_dupla(f"{nome_forma}:", moeda_br(valor)))
        # --- Movimentações Financeiras ---
        # elements.append(Spacer(1, 8))
        # elements.append(linha_separadora())
        # elements.append(Paragraph("MOVIMENTAÇÕES", subtitle_style))
        # elements.append(Spacer(1, 6))
        # elements.append(linha_separadora())
        # for mov in movimentacoes:
        #     tipo_cat = f"{mov.tipo.value}"
        #     if mov.categoria:
        #         tipo_cat += f" - {mov.categoria.value}"
        #     elements.append(linha_dupla(tipo_cat, moeda_br(float(mov.valor))))
        #     if mov.descricao:
        #         descricao = mov.descricao
        #         if len(descricao) > 25:
        #             words = descricao
        #             lines = []
        #             current_line = ""
        #             for word in words:
        #                 if len(current_line + word) > 25:
        #                     lines.append(current_line)
        #                     current_line = word + ""
        #                 else:
        #                     current_line += word + ""
        #             if current_line:
        #                 lines.append(current_line)
        #             for line in lines:
        #                 elements.append(Paragraph(line, normal_style))
        #         else:
        #             elements.append(Paragraph(descricao, normal_style))
        #     elements.append(linha_separadora())

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

        response = make_response(
            send_file(
                buffer,
                mimetype="application/pdf",
                as_attachment=False,
                download_name=f"caixa_{caixa_id}_bobina.pdf",
            )
        )
        response.headers["Content-Disposition"] = (
            f"inline; filename=caixa_{caixa_id}_bobina.pdf"
        )
        return response

    except Exception as e:
        logger.error(f"Erro ao gerar PDF do caixa {caixa_id}: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        session.close()


@admin_bp.route("/caixas/<int:caixa_id>/aprovar", methods=["POST"])
@login_required
@admin_required
def aprovar_caixa(caixa_id):
    """Aprova o caixa e transfere automaticamente os valores (incluindo contas a prazo pagas) do operador para o admin."""
    try:
        caixa = Caixa.query.get_or_404(caixa_id)
        operador = caixa.operador

        if not operador or not operador.conta:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Operador ou conta do operador não encontrado",
                    }
                ),
                404,
            )

        conta_origem = operador.conta
        conta_destino = current_user.conta

        if not conta_destino:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Administrador não possui conta vinculada",
                    }
                ),
                400,
            )

        valores_caixa = calcular_formas_pagamento(caixa_id, db.session)

        formas_pagamento_validas = [
            "dinheiro",
            "pix_loja",
            "pix_fabiano",
            "pix_edfrance",
            "pix_maquineta",
            "cartao_debito",
            "cartao_credito",
        ]

        # --- Vendas normais ---
        vendas_por_forma = valores_caixa.get("vendas_por_forma_pagamento", {})
        formas_transferir = {
            forma: Decimal(str(valor))
            for forma, valor in vendas_por_forma.items()
            if forma in formas_pagamento_validas and valor > 0
        }

        # --- Contas a prazo recebidas ---
        pagamentos_contas = valores_caixa.get("a_prazo_recebido", [])
        for forma_enum, valor in pagamentos_contas:
            if valor > 0:
                forma = forma_enum.value
                if forma in formas_pagamento_validas:
                    formas_transferir[forma] = formas_transferir.get(
                        forma, Decimal("0.00")
                    ) + Decimal(valor)

        if not formas_transferir:
            return (
                jsonify(
                    {"success": False, "error": "Nenhum valor válido para transferir"}
                ),
                400,
            )

        total_transferido = Decimal("0.00")

        # --- Transfere valores por forma de pagamento ---
        for forma_str, valor in formas_transferir.items():
            try:
                forma_pagamento_enum = FormaPagamento(forma_str)
            except ValueError:
                continue

            valor = Decimal(str(valor))
            if valor <= 0:
                continue

            # --- Atualiza origem ---
            saldo_fp_origem = next(
                (
                    s
                    for s in conta_origem.saldos_forma_pagamento
                    if s.forma_pagamento == forma_pagamento_enum
                ),
                None,
            )
            if not saldo_fp_origem:
                saldo_fp_origem = SaldoFormaPagamento(
                    conta_id=conta_origem.id,
                    forma_pagamento=forma_pagamento_enum,
                    saldo=Decimal("0.00"),
                )
                db.session.add(saldo_fp_origem)

            saldo_fp_origem.saldo = max(saldo_fp_origem.saldo - valor, 0)
            saldo_fp_origem.sincronizado = False

            mov_saida = MovimentacaoConta(
                conta_id=conta_origem.id,
                tipo=TipoMovimentacao.transferencia,
                forma_pagamento=forma_pagamento_enum,
                valor=valor,
                descricao=f"Transferência automática - Caixa {caixa_id} aprovado para {current_user.nome}",
                usuario_id=current_user.id,
                caixa_id=caixa.id,
                data=datetime.now(),
            )
            db.session.add(mov_saida)

            # --- Atualiza destino ---
            saldo_fp_destino = next(
                (
                    s
                    for s in conta_destino.saldos_forma_pagamento
                    if s.forma_pagamento == forma_pagamento_enum
                ),
                None,
            )
            if not saldo_fp_destino:
                saldo_fp_destino = SaldoFormaPagamento(
                    conta_id=conta_destino.id,
                    forma_pagamento=forma_pagamento_enum,
                    saldo=Decimal("0.00"),
                )
                db.session.add(saldo_fp_destino)

            saldo_fp_destino.saldo += valor
            saldo_fp_destino.sincronizado = False

            mov_entrada = MovimentacaoConta(
                conta_id=conta_destino.id,
                tipo=TipoMovimentacao.entrada,
                forma_pagamento=forma_pagamento_enum,
                valor=valor,
                descricao=f"Crédito automático - Caixa {caixa_id} do operador {operador.nome}",
                usuario_id=current_user.id,
                caixa_id=caixa.id,
                data=datetime.now(),
            )
            db.session.add(mov_entrada)

            total_transferido += valor

        # --- Atualiza saldo total das contas diretamente ---
        conta_origem.saldo_total = max(
            Decimal(str(conta_origem.saldo_total)) - total_transferido, 0
        )
        conta_destino.saldo_total = (
            Decimal(str(conta_destino.saldo_total)) + total_transferido
        )

        conta_origem.sincronizado = False
        conta_destino.sincronizado = False

        # --- Atualiza status do caixa ---
        caixa.status = StatusCaixa.aprovado
        caixa.valor_confirmado = float(total_transferido)
        caixa.aprovado_por_id = current_user.id
        caixa.data_aprovacao = datetime.now()

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Caixa {caixa.id} aprovado com sucesso. Transferência total de R$ {total_transferido:.2f}.",
                    "total_transferido": float(total_transferido),
                    "formas_transferidas": {
                        k: float(v) for k, v in formas_transferir.items()
                    },
                    "status": caixa.status.value,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao aprovar caixa {caixa_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/caixas/<int:caixa_id>/recusar", methods=["POST"])
@login_required
@admin_required
def recusar_caixa(caixa_id):
    """Rota para recusar o fechamento de um caixa"""
    caixa = Caixa.query.get_or_404(caixa_id)

    if current_user.tipo != "admin":
        logger.warning(f"Usuário não autorizado a recusar caixa: {current_user.nome}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Apenas administradores podem recusar caixas",
                }
            ),
            403,
        )

    data = request.get_json()
    motivo = data.get("motivo")
    valor_correto = data.get("valor_correto")

    if not motivo:
        logger.warning("Motivo da recusa não fornecido")
        return (
            jsonify({"success": False, "error": "Motivo da recusa é obrigatório"}),
            400,
        )

    try:
        caixa.rejeitar_fechamento(
            administrador_id=current_user.id, motivo=motivo, valor_correto=valor_correto
        )
        db.session.commit()
        logger.info(
            f"Caixa {caixa_id} recusado com sucesso pelo usuário {current_user.nome}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Caixa recusado com sucesso",
                    "status": caixa.status.value,
                    "observacoes_admin": caixa.observacoes_admin,
                }
            ),
            200,
        )
    except ValueError as e:
        logger.error(f"Erro ao recusar caixa {caixa_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao recusar caixa {caixa_id}: {str(e)}")
        db.session.rollback()
        return (
            jsonify({"success": False, "error": f"Erro ao recusar caixa: {str(e)}"}),
            500,
        )


@admin_bp.route("/caixas/<int:caixa_id>/enviar_analise", methods=["POST"])
@login_required
@admin_required
def enviar_para_analise(caixa_id):
    """Rota para enviar um caixa para análise (fechamento inicial)"""

    try:
        caixa = Caixa.query.get_or_404(caixa_id)
        logger.info(f"Caixa encontrado: {caixa.id}, status: {caixa.status}")

        data = request.get_json()

        valor_fechamento = data.get("valor_fechamento")
        observacoes = data.get("observacoes")

        if not valor_fechamento:
            logger.warning(f"Valor de fechamento não fornecido para caixa {caixa_id}")
            return jsonify({"error": "Valor de fechamento é obrigatório"}), 400

        caixa.fechar_caixa(
            valor_fechamento=valor_fechamento,
            observacoes_operador=observacoes,
            usuario_id=current_user.id,
        )
        db.session.commit()
        logger.info(
            f"Caixa {caixa_id} enviado para análise com sucesso pelo usuário {current_user.nome}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Caixa enviado para análise com sucesso",
                    "status": caixa.status.value,
                    "valor_fechamento": float(caixa.valor_fechamento),
                }
            ),
            200,
        )

    except ValueError as e:
        logger.error(f"Erro ao enviar caixa {caixa_id} para análise: {str(e)}")
        logger.warning(f"Erro de valor: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Erro ao enviar caixa para análise: {str(e)}",
                }
            ),
            500,
        )


@admin_bp.route("/caixas/<int:caixa_id>/reabrir", methods=["POST"])
@login_required
@admin_required
def reabrir_caixa(caixa_id):
    """Rota para reabrir um caixa fechado ou recusado"""
    caixa = Caixa.query.get_or_404(caixa_id)

    if current_user.tipo != "admin":
        logger.warning(f"Usuário não autorizado a reabrir caixa: {current_user.nome}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Apenas administradores podem reabrir caixas",
                }
            ),
            403,
        )

    data = request.get_json()
    motivo = data.get("motivo")

    try:
        caixa.reabrir_caixa(administrador_id=current_user.id, motivo=motivo)
        db.session.commit()
        logger.info(
            f"Caixa {caixa_id} reaberto com sucesso pelo usuário {current_user.nome}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Caixa reaberto com sucesso",
                    "status": caixa.status.value,
                }
            ),
            200,
        )
    except ValueError as e:
        logger.error(f"Erro ao reabrir caixa {caixa_id}: {str(e)}")
        logger.warning(f"Erro de valor: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro interno: {str(e)}")
        db.session.rollback()
        return (
            jsonify({"success": False, "error": f"Erro ao reabrir caixa: {str(e)}"}),
            500,
        )


# =============== RELATÓRIO DE SAIDA DE PRODUTOS ======================
from flask import jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from zoneinfo import ZoneInfo


@admin_bp.route("/relatorios/vendas-produtos", methods=["GET"])
@login_required
@admin_required
def relatorio_vendas_produtos():
    try:
        # Obter parâmetros de filtro da requisição
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        produto_nome = request.args.get("produto_nome")
        produto_codigo = request.args.get("produto_codigo")
        categoria = request.args.get("categoria")
        limite = request.args.get("limite", default=50, type=int)

        # Definir datas padrão (últimos 30 dias) se não fornecidas
        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        if not data_inicio:
            data_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
        if not data_fim:
            data_fim = hoje.strftime("%Y-%m-%d")

        # Converter strings para objetos date
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            logger.warning("Formato de data inválido fornecido")
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400

        # Construir a query base para produtos vendidos
        query = (
            db.session.query(
                Produto.id.label("produto_id"),
                Produto.nome.label("produto_nome"),
                Produto.codigo.label("produto_codigo"),
                Produto.unidade.label("unidade"),
                func.sum(NotaFiscalItem.quantidade).label("quantidade_vendida"),
                func.sum(NotaFiscalItem.valor_total).label("valor_total_vendido"),
                func.sum(
                    NotaFiscalItem.quantidade * Produto.valor_unitario_compra
                ).label("custo_total"),
                Produto.estoque_loja.label("estoque_atual_loja"),
                Produto.estoque_minimo.label("estoque_minimo"),
            )
            .join(NotaFiscalItem, NotaFiscalItem.produto_id == Produto.id)
            .join(NotaFiscal, NotaFiscal.id == NotaFiscalItem.nota_id)
            .filter(
                NotaFiscal.status == StatusNota.emitida,
                NotaFiscal.data_emissao >= data_inicio,
                NotaFiscal.data_emissao
                <= data_fim + timedelta(days=1),  # Inclui todo o dia final
            )
            .group_by(Produto.id)
            .order_by(Produto.nome.asc(), func.sum(NotaFiscalItem.quantidade).desc())
        )

        # Aplicar filtros adicionais
        if produto_nome:
            query = query.filter(Produto.nome.ilike(f"%{produto_nome}%"))

        if produto_codigo:
            query = query.filter(Produto.codigo.ilike(f"%{produto_codigo}%"))

        if categoria:
            query = query.filter(Produto.tipo == categoria)

        # Limitar resultados se necessário
        if limite:
            query = query.limit(limite)

        # Executar a query
        resultados = query.all()

        # Calcular despesas e estornos no período
        despesas_query = (
            db.session.query(func.sum(Financeiro.valor).label("total_despesas"))
            .filter(
                Financeiro.tipo == TipoMovimentacao.saida,
                Financeiro.categoria == CategoriaFinanceira.despesa,
                Financeiro.data >= data_inicio,
                Financeiro.data <= data_fim + timedelta(days=1),
            )
            .first()
        )

        estornos_query = (
            db.session.query(func.sum(Financeiro.valor).label("total_estornos"))
            .filter(
                Financeiro.tipo == TipoMovimentacao.saida_estorno,
                Financeiro.data >= data_inicio,
                Financeiro.data <= data_fim + timedelta(days=1),
            )
            .first()
        )

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

            relatorio.append(
                {
                    "produto_id": r.produto_id,
                    "produto_nome": r.produto_nome,
                    "produto_codigo": r.produto_codigo,
                    "unidade": r.unidade.value,
                    "quantidade_vendida": float(r.quantidade_vendida),
                    "valor_total_vendido": valor_total_vendido,
                    "custo_total": custo_total,
                    "lucro_bruto": lucro_bruto,
                    "margem_lucro": (
                        (lucro_bruto / valor_total_vendido * 100)
                        if valor_total_vendido > 0
                        else 0
                    ),
                    "estoque_atual_loja": float(r.estoque_atual_loja),
                    "estoque_minimo": float(r.estoque_minimo),
                    "percentual_estoque": round(percentual_estoque, 2),
                    "status_estoque": (
                        "CRÍTICO" if r.estoque_atual_loja < r.estoque_minimo else "OK"
                    ),
                    "dias_restantes": (
                        round(r.estoque_atual_loja / (r.quantidade_vendida / 30), 2)
                        if r.quantidade_vendida > 0
                        else None
                    ),
                }
            )

        # --- APLICAR AJUSTE DE DIFERENÇAS DE CAIXA ---
        soma_ajuste_caixa = 0.0
        try:
            caixas = Caixa.query.filter(
                Caixa.data_fechamento != None,
                Caixa.data_fechamento
                >= datetime.combine(data_inicio, datetime.min.time()),
                Caixa.data_fechamento
                <= datetime.combine(data_fim, datetime.max.time()),
            ).all()

            for c in caixas:
                abertura = (
                    float(c.valor_abertura) if c.valor_abertura is not None else 0.0
                )

                # preferir valor_fechamento; se não houver, usar valor_confirmado; se ambos None usar 0
                if c.valor_fechamento is not None:
                    fechamento = float(c.valor_fechamento)
                elif c.valor_confirmado is not None:
                    fechamento = float(c.valor_confirmado)
                else:
                    fechamento = 0.0

                # Ajuste: abertura - fechamento
                #  - se fechamento > abertura => ajuste negativo (deduzir)
                #  - se fechamento < abertura => ajuste positivo (somar)
                ajuste = abertura - fechamento
                soma_ajuste_caixa += ajuste

        except Exception:
            logger.exception(
                "Erro ao calcular diferenças de caixa; prosseguindo sem ajuste."
            )
            soma_ajuste_caixa = 0.0

        # Aplicar ajuste ao lucro bruto
        # lucro_bruto_total_ajustado = lucro_bruto_total + soma_ajuste_caixa
        lucro_bruto_total_ajustado = lucro_bruto_total + float(soma_ajuste_caixa)

        # Calcular lucro líquido total com base no lucro bruto ajustado
        lucro_liquido_total = (
            lucro_bruto_total_ajustado - float(total_despesas) - float(total_estornos)
        )

        # Adicionar totais ao relatório
        total_vendido = sum(item["valor_total_vendido"] for item in relatorio)
        total_quantidade = sum(item["quantidade_vendida"] for item in relatorio)
        total_custo = sum(item["custo_total"] for item in relatorio)

        meta_relatorio = {
            "data_inicio": data_inicio.strftime("%Y-%m-%d"),
            "data_fim": data_fim.strftime("%Y-%m-%d"),
            "total_produtos": len(relatorio),
            "total_quantidade_vendida": round(total_quantidade, 2),
            "total_valor_vendido": total_vendido,
            "total_custo": total_custo,
            "lucro_bruto": lucro_bruto_total,
            "lucro_bruto_ajustado": lucro_bruto_total_ajustado,
            "lucro_liquido": lucro_liquido_total,
            "produtos_estoque_critico": sum(
                1 for item in relatorio if item["status_estoque"] == "CRÍTICO"
            ),
        }

        return jsonify({"meta": meta_relatorio, "dados": relatorio})

    except Exception as e:
        logger.error(
            f"Erro ao gerar relatório de vendas de produtos: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/relatorios/vendas-diarias", methods=["GET"])
@login_required
@admin_required
def relatorio_vendas_diarias():
    try:
        # Obter parâmetros de filtro
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        agrupar_por = request.args.get(
            "agrupar_por", default="dia"
        )  # 'dia', 'semana', 'mes'

        # Definir datas padrão (últimos 30 dias)
        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        if not data_inicio:
            data_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
        if not data_fim:
            data_fim = hoje.strftime("%Y-%m-%d")

        # Converter strings para objetos date
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            logger.warning("Formato de data inválido fornecido")
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400

        # Definir a expressão de agrupamento baseada no parâmetro
        if agrupar_por == "dia":
            group_expr = func.date(NotaFiscal.data_emissao)
            label_format = "%Y-%m-%d"
        elif agrupar_por == "semana":
            group_expr = func.date_trunc("week", NotaFiscal.data_emissao)
            label_format = "Semana %Y-%m-%d"
        elif agrupar_por == "mes":
            group_expr = func.date_trunc("month", NotaFiscal.data_emissao)
            label_format = "%Y-%m"
        else:
            logger.warning("Agrupamento inválido fornecido")
            return (
                jsonify({"error": "Agrupamento inválido. Use dia, semana ou mes"}),
                400,
            )

        # Query para obter vendas agrupadas por período
        vendas_por_periodo = (
            db.session.query(
                group_expr.label("periodo"),
                func.count(NotaFiscal.id).label("quantidade_vendas"),
                func.sum(NotaFiscal.valor_total).label("valor_total"),
                func.sum(NotaFiscal.valor_desconto).label("valor_desconto_total"),
            )
            .filter(
                NotaFiscal.status == StatusNota.emitida,
                NotaFiscal.data_emissao >= data_inicio,
                NotaFiscal.data_emissao <= data_fim + timedelta(days=1),
            )
            .group_by(group_expr)
            .order_by(group_expr)
            .all()
        )

        # Query para obter produtos mais vendidos no período
        produtos_mais_vendidos = (
            db.session.query(
                Produto.id,
                Produto.nome,
                func.sum(NotaFiscalItem.quantidade).label("quantidade_total"),
                func.sum(NotaFiscalItem.valor_total).label("valor_total"),
            )
            .join(NotaFiscalItem, NotaFiscalItem.produto_id == Produto.id)
            .join(NotaFiscal, NotaFiscal.id == NotaFiscalItem.nota_id)
            .filter(
                NotaFiscal.status == StatusNota.emitida,
                NotaFiscal.data_emissao >= data_inicio,
                NotaFiscal.data_emissao <= data_fim + timedelta(days=1),
            )
            .group_by(Produto.id)
            .order_by(func.sum(NotaFiscalItem.quantidade).desc())
            .limit(5)
            .all()
        )

        # Processar resultados
        relatorio_periodo = [
            {
                "periodo": r.periodo.strftime(label_format),
                "quantidade_vendas": r.quantidade_vendas,
                "valor_total": float(r.valor_total),
                "valor_desconto_total": float(r.valor_desconto_total),
                "valor_liquido": float(r.valor_total - r.valor_desconto_total),
            }
            for r in vendas_por_periodo
        ]

        relatorio_produtos = [
            {
                "produto_id": r.id,
                "produto_nome": r.nome,
                "quantidade_total": float(r.quantidade_total),
                "valor_total": float(r.valor_total),
            }
            for r in produtos_mais_vendidos
        ]

        return jsonify(
            {
                "meta": {
                    "data_inicio": data_inicio.strftime("%Y-%m-%d"),
                    "data_fim": data_fim.strftime("%Y-%m-%d"),
                    "agrupar_por": agrupar_por,
                },
                "vendas_por_periodo": relatorio_periodo,
                "produtos_mais_vendidos": relatorio_produtos,
            }
        )

    except Exception as e:
        logger.error(
            f"Erro ao gerar relatório de vendas diárias: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/relatorios/vendas-produtos/exportar", methods=["GET"])
@login_required
@admin_required
def exportar_relatorio_vendas_produtos():
    try:
        # Os mesmos parâmetros da rota /relatorios/vendas-produtos
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        produto_id = request.args.get("produto_id")
        categoria = request.args.get("categoria")
        limite = request.args.get("limite", default=50, type=int)

        # Chame a função existente para obter os dados
        relatorio = relatorio_vendas_produtos().get_json()

        # Crie um arquivo CSV ou Excel (exemplo simplificado)
        output = io.StringIO()
        writer = csv.writer(output)

        # Escreva o cabeçalho
        writer.writerow(
            [
                "ID Produto",
                "Nome Produto",
                "Unidade",
                "Quantidade Vendida",
                "Valor Total Vendido",
                "Estoque Atual Loja",
                "Estoque Mínimo",
                "Status Estoque",
                "Dias Restantes",
            ]
        )

        # Escreva os dados
        for item in relatorio["dados"]:
            writer.writerow(
                [
                    item["produto_id"],
                    item["produto_nome"],
                    item["unidade"],
                    item["quantidade_vendida"],
                    item["valor_total_vendido"],
                    item["estoque_atual_loja"],
                    item["estoque_minimo"],
                    item["status_estoque"],
                    item["dias_restantes"] or "",
                ]
            )

        # Retorne o arquivo para download
        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={
                "Content-disposition": "attachment; filename=relatorio_saidas_produtos.csv"
            },
        )

    except Exception as e:
        logger.error(
            f"Erro ao exportar relatório de vendas de produtos: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/produtos/categorias", methods=["GET"])
@login_required
@admin_required
def get_produto_categorias():
    try:
        # Query distinct product categories from the database
        categorias = db.session.query(Produto.tipo).distinct().all()

        # Extract just the category names from the query results
        categorias_list = [categoria[0] for categoria in categorias if categoria[0]]

        return jsonify(
            {"categorias": sorted(categorias_list)}  # Return sorted list of categories
        )
    except Exception as e:
        logger.error(f"Erro ao obter categorias de produtos: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/relatorios/vendas-produtos/detalhes", methods=["GET"])
@login_required
@admin_required
def relatorio_vendas_produtos_detalhes():
    try:
        # Obter parâmetros de filtro
        produto_id = request.args.get("produto_id")
        produto_nome = request.args.get("produto_nome")
        produto_codigo = request.args.get("produto_codigo")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        # Validação básica dos parâmetros
        if not any([produto_id, produto_nome, produto_codigo]):
            logger.warning("Nenhum filtro de produto fornecido")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "É necessário fornecer pelo menos um filtro (ID, nome ou código do produto)",
                    }
                ),
                400,
            )

        # Conversão de datas com tratamento de erros
        data_inicio_obj = None
        data_fim_obj = None
        try:
            if data_inicio and data_inicio.lower() != "undefined":
                data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            if data_fim and data_fim.lower() != "undefined":
                data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            logger.warning("Formato de data inválido fornecido")
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400

        # Converter para datetime para filtros
        data_inicio_dt = (
            datetime.combine(data_inicio_obj, datetime.min.time())
            if data_inicio_obj
            else None
        )
        data_fim_dt = (
            datetime.combine(data_fim_obj, datetime.max.time())
            if data_fim_obj
            else None
        )

        # Construir query base
        produto_query = (
            db.session.query(
                Produto.id.label("produto_id"),
                Produto.nome.label("produto_nome"),
                Produto.codigo.label("produto_codigo"),
                Produto.tipo.label("produto_tipo"),
                Produto.unidade.label("unidade"),
                func.sum(NotaFiscalItem.quantidade).label("quantidade_vendida"),
                func.sum(NotaFiscalItem.valor_total).label("valor_total_vendido"),
                Produto.estoque_loja.label("estoque_atual_loja"),
                Produto.estoque_minimo.label("estoque_minimo"),
            )
            .join(NotaFiscalItem, NotaFiscalItem.produto_id == Produto.id)
            .join(NotaFiscal, NotaFiscal.id == NotaFiscalItem.nota_id)
            .filter(NotaFiscal.status == StatusNota.emitida)
        )

        # Aplicar filtros do produto
        if produto_id:
            produto_query = produto_query.filter(Produto.id == produto_id)
        if produto_nome:
            produto_query = produto_query.filter(
                Produto.nome.ilike(f"%{produto_nome}%")
            )
        if produto_codigo:
            produto_query = produto_query.filter(
                Produto.codigo.ilike(f"%{produto_codigo}%")
            )

        # Aplicar filtros de data
        if data_inicio_dt:
            produto_query = produto_query.filter(
                NotaFiscal.data_emissao >= data_inicio_dt
            )
        if data_fim_dt:
            produto_query = produto_query.filter(NotaFiscal.data_emissao <= data_fim_dt)

        # Executar query
        produto_info = produto_query.group_by(Produto.id).first()

        if not produto_info:
            logger.info("Nenhum produto encontrado com os filtros fornecidos")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Nenhum produto encontrado com os filtros fornecidos",
                    }
                ),
                404,
            )

        # Calcular métricas adicionais
        status_estoque = (
            "CRÍTICO"
            if produto_info.estoque_atual_loja < produto_info.estoque_minimo
            else "OK"
        )

        dias_restantes = None
        if produto_info.quantidade_vendida and produto_info.quantidade_vendida > 0:
            periodo_dias = 30  # Período padrão para cálculo
            if data_inicio_obj and data_fim_obj:
                periodo_dias = (data_fim_obj - data_inicio_obj).days or 30
            media_diaria = produto_info.quantidade_vendida / periodo_dias
            dias_restantes = (
                round(produto_info.estoque_atual_loja / media_diaria, 2)
                if media_diaria > 0
                else None
            )

        # Obter histórico detalhado de vendas
        historico_query = (
            db.session.query(
                NotaFiscal.data_emissao,
                NotaFiscalItem.quantidade,
                NotaFiscalItem.valor_unitario,
                NotaFiscalItem.valor_total,
                Cliente.nome.label("cliente_nome"),
            )
            .join(NotaFiscal, NotaFiscal.id == NotaFiscalItem.nota_id)
            .outerjoin(Cliente, Cliente.id == NotaFiscal.cliente_id)
            .filter(
                NotaFiscalItem.produto_id == produto_info.produto_id,
                NotaFiscal.status == StatusNota.emitida,
            )
        )

        # Aplicar filtros de data no histórico
        if data_inicio_dt:
            historico_query = historico_query.filter(
                NotaFiscal.data_emissao >= data_inicio_dt
            )
        if data_fim_dt:
            historico_query = historico_query.filter(
                NotaFiscal.data_emissao <= data_fim_dt
            )

        historico = (
            historico_query.order_by(NotaFiscal.data_emissao.desc()).limit(50).all()
        )

        # Formatar resposta
        return jsonify(
            {
                "success": True,
                "produto": {
                    "produto_id": produto_info.produto_id,
                    "produto_nome": produto_info.produto_nome,
                    "produto_codigo": produto_info.produto_codigo,
                    "produto_tipo": produto_info.produto_tipo,
                    "unidade": produto_info.unidade.value,
                    "quantidade_vendida": float(produto_info.quantidade_vendida),
                    "valor_total_vendido": float(produto_info.valor_total_vendido),
                    "estoque_atual_loja": float(produto_info.estoque_atual_loja),
                    "estoque_minimo": float(produto_info.estoque_minimo),
                    "status_estoque": status_estoque,
                    "dias_restantes": dias_restantes,
                },
                "historico": [
                    {
                        "data_emissao": item.data_emissao.isoformat(),
                        "quantidade": float(item.quantidade),
                        "valor_unitario": float(item.valor_unitario),
                        "valor_total": float(item.valor_total),
                        "cliente_nome": item.cliente_nome,
                    }
                    for item in historico
                ],
            }
        )

    except Exception as e:
        logger.error(
            f"Erro ao gerar relatório de vendas detalhado: {str(e)}", exc_info=True
        )
        return jsonify({"success": False, "message": "Erro interno no servidor"}), 500


@admin_bp.route("/relatorios/vendas-produtos/pdf", methods=["GET"])
@login_required
@admin_required
def relatorio_vendas_produtos_pdf():
    try:
        relatorio_data = relatorio_vendas_produtos().get_json()
        if "error" in relatorio_data:
            logger.error(f"Erro ao obter dados para PDF: {relatorio_data['error']}")
            return jsonify(relatorio_data), 500

        data_inicio = datetime.strptime(
            relatorio_data["meta"]["data_inicio"], "%Y-%m-%d"
        )
        data_fim = datetime.strptime(relatorio_data["meta"]["data_fim"], "%Y-%m-%d")
        data_inicio_fmt = data_inicio.strftime("%d/%m/%Y")
        data_fim_fmt = data_fim.strftime("%d/%m/%Y")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=10 * mm,
            bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # -------------------- Cabeçalho --------------------
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
        elements.append(Paragraph("📊 Relatório de Vendas de Produtos", header_style))
        elements.append(
            Paragraph(f"Período: {data_inicio_fmt} a {data_fim_fmt}", styles["Normal"])
        )
        elements.append(Spacer(1, 8))
        elements.append(
            Table(
                [["" * 80]],
                colWidths=[170 * mm],
                style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.black)],
            )
        )
        elements.append(Spacer(1, 12))

        # -------------------- Resumo em tabela --------------------
        resumo_data = [
            [
                "Produtos",
                "Qtd. Vendida",
                "Valor Total",
                "Custo Total",
                "Lucro Bruto",
                "Lucro Líquido",
            ],
            [
                str(relatorio_data["meta"]["total_produtos"]),
                str(relatorio_data["meta"]["total_quantidade_vendida"]),
                formatarMoeda(relatorio_data["meta"]["total_valor_vendido"]),
                formatarMoeda(relatorio_data["meta"]["total_custo"]),
                formatarMoeda(relatorio_data["meta"]["lucro_bruto"]),
                formatarMoeda(relatorio_data["meta"]["lucro_liquido"]),
            ],
        ]

        resumo_table = Table(
            resumo_data,
            colWidths=[25 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm],
        )
        resumo_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONT", (0, 1), (-1, 1), "Helvetica", 9),
            ]
        )
        resumo_table.setStyle(resumo_style)
        elements.append(resumo_table)
        elements.append(Spacer(1, 18))

        # -------------------- Tabela de produtos --------------------
        produto_id = request.args.get("produto_id")
        if not produto_id:
            elements.append(Paragraph("📦 Lista de Produtos", styles["Heading2"]))
            elements.append(Spacer(1, 8))

            if relatorio_data["dados"]:
                table_data = [
                    [
                        "ID",
                        "Produto",
                        "Unid.",
                        "Qtd.",
                        "Vendas",
                        "Custo",
                        "Lucro",
                        "Estoque",
                    ]
                ]

                for produto in relatorio_data["dados"]:
                    nome_produto = produto["produto_nome"]
                    if len(nome_produto) > 40:
                        nome_produto = nome_produto[:37] + "..."
                    table_data.append(
                        [
                            str(produto["produto_id"]),
                            nome_produto,
                            produto["unidade"],
                            str(round(produto["quantidade_vendida"], 2)),
                            formatarMoeda(produto["valor_total_vendido"]),
                            formatarMoeda(produto["custo_total"]),
                            formatarMoeda(produto["lucro_bruto"]),
                            str(round(produto["estoque_atual_loja"], 2)),
                        ]
                    )

                # Linha de totais
                table_data.append(
                    [
                        "",
                        "TOTAL GERAL",
                        "",
                        "",
                        formatarMoeda(relatorio_data["meta"]["total_valor_vendido"]),
                        formatarMoeda(relatorio_data["meta"]["total_custo"]),
                        formatarMoeda(relatorio_data["meta"]["lucro_bruto"]),
                        "",
                    ]
                )

                col_widths = [
                    15 * mm,
                    60 * mm,
                    15 * mm,
                    15 * mm,
                    25 * mm,
                    25 * mm,
                    25 * mm,
                    15 * mm,
                ]
                produto_table = Table(table_data, colWidths=col_widths, repeatRows=1)

                table_style = TableStyle(
                    [
                        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("ALIGN", (1, 1), (1, -1), "LEFT"),
                        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        # Linha total
                        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 9),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                    ]
                )

                # Linhas zebradas
                for i in range(1, len(table_data) - 1):
                    if i % 2 == 0:
                        table_style.add(
                            "BACKGROUND", (0, i), (-1, i), colors.whitesmoke
                        )

                # Cores lucro
                for i, produto in enumerate(relatorio_data["dados"], start=1):
                    lucro = produto["lucro_bruto"]
                    if lucro < 0:
                        table_style.add("TEXTCOLOR", (6, i), (6, i), colors.red)
                    else:
                        table_style.add("TEXTCOLOR", (6, i), (6, i), colors.darkgreen)

                # Lucro total
                if relatorio_data["meta"]["lucro_bruto"] < 0:
                    table_style.add("TEXTCOLOR", (6, -1), (6, -1), colors.red)
                else:
                    table_style.add("TEXTCOLOR", (6, -1), (6, -1), colors.darkgreen)

                produto_table.setStyle(table_style)
                elements.append(produto_table)

        # -------------------- Rodapé --------------------
        elements.append(Spacer(1, 15))
        rodape = datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M")
        elements.append(
            Paragraph(
                rodape,
                ParagraphStyle(
                    "Rodape", fontSize=8, alignment=TA_RIGHT, textColor=colors.grey
                ),
            )
        )

        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            "inline; filename=relatorio_vendas_produtos.pdf"
        )
        return response

    except Exception as e:
        logger.error(
            f"Erro ao gerar PDF do relatório de vendas de produtos: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500

# ================= CONTAS A RECEBER =====================
from app.crud import obter_contas_receber


@admin_bp.route("/contas-receber", methods=["GET"])
@login_required
@admin_required
def contas_receber():
    clientes, totais = obter_contas_receber(
        cliente_nome=request.args.get("cliente_nome"),
        cliente_documento=request.args.get("cliente_documento"),
        data_emissao_inicio=request.args.get("data_emissao_inicio"),
        data_emissao_fim=request.args.get("data_emissao_fim"),
        status=request.args.get("status"),
    )

    total_contas = sum(len(c["contas"]) for c in clientes)

    return jsonify(
        {
            "success": True,
            "clientes_agrupados": clientes,
            "total_clientes": len(clientes),
            "total_contas": total_contas,
            "totais_gerais": totais,
        }
    )


@admin_bp.route("/contas-receber/pdf", methods=["GET"])
@login_required
@admin_required
def contas_receber_pdf():
    clientes, totais = obter_contas_receber(
        cliente_nome=request.args.get("cliente_nome"),
        cliente_documento=request.args.get("cliente_documento"),
        data_emissao_inicio=request.args.get("data_emissao_inicio"),
        data_emissao_fim=request.args.get("data_emissao_fim"),
        status=request.args.get("status"),
    )

    html = render_template(
        "relatorio_contasReceber.html",
        clientes=clientes,
        totais=totais,
        data_emissao=datetime.now(),
        periodo=f"{request.args.get('data_emissao_inicio','-')} até {request.args.get('data_emissao_fim','-')}",
        usuario=current_user.nome,
    )

    pdf_buffer = BytesIO()
    HTML(string=html, base_url=current_app.root_path).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        download_name="relatorio_contas_receber.pdf",
    )


@admin_bp.route("/contas-receber/<int:id>/detalhes", methods=["GET"])
@login_required
@admin_required
def conta_receber_detalhes(id):
    conta = ContaReceber.query.get_or_404(id)

    pagamento_efetuados = (
        PagamentoContaReceber.query.filter(PagamentoContaReceber.conta_id == conta.id)
        .order_by(PagamentoContaReceber.data_pagamento.asc())
        .all()
    )

    caixas = Caixa.query.order_by(Caixa.data_abertura.desc()).all()
    caixas_json = [
        {
            "id": c.id,
            "operador": c.operador.nome if c.operador else "Sem operador",
            "data_abertura": c.data_abertura.strftime("%Y-%m-%d"),
            "status": c.status.value,
        }
        for c in caixas
    ]

    nota = conta.nota_fiscal

    nota_json = None
    if nota:
        nota_json = {
            "id": nota.id,
            "status": nota.status.value,
            "data_emissao": nota.data_emissao.strftime("%d/%m/%Y"),
            "forma_pagamento": (
                nota.forma_pagamento.value if nota.forma_pagamento else None
            ),
            "valor_total": float(nota.valor_total),
            "valor_desconto": float(nota.valor_desconto),
            "valor_recebido": (
                float(nota.valor_recebido) if nota.valor_recebido else 0.0
            ),
            "troco": float(nota.troco) if nota.troco else 0.0,
            "a_prazo": nota.a_prazo,
            "cliente": {
                "id": nota.cliente.id if nota.cliente else None,
                "nome": nota.cliente.nome if nota.cliente else None,
                "documento": nota.cliente.documento if nota.cliente else None,
            },
            "operador": {"id": nota.operador.id, "nome": nota.operador.nome},
            # ---- ITENS / PRODUTOS DA NOTA ----
            "itens": [
                {
                    "id": item.id,
                    "produto_id": item.produto_id,
                    "produto": item.produto.nome,
                    "quantidade": float(item.quantidade),
                    "valor_unitario": float(item.valor_unitario),
                    "valor_total": float(item.valor_total),
                    "desconto_aplicado": float(item.desconto_aplicado or 0),
                    "tipo_desconto": (
                        item.tipo_desconto.value if item.tipo_desconto else None
                    ),
                }
                for item in nota.itens
            ],
            # ---- PAGAMENTOS FEITOS NA NOTA ----
            "pagamentos_nota": [
                {
                    "id": p.id,
                    "forma_pagamento": p.forma_pagamento.value,
                    "valor": float(p.valor),
                    "data": p.data.strftime("%d/%m/%Y %H:%M"),
                }
                for p in nota.pagamentos
            ],
            "total_pago_na_nota": float(sum(p.valor for p in nota.pagamentos)),
        }

    return jsonify(
        {
            # ---- CONTA A RECEBER ----
            "id": conta.id,
            "descricao": conta.descricao,
            "status": conta.status.value,
            "valor_original": float(conta.valor_original),
            "valor_aberto": float(conta.valor_aberto),
            "data_emissao": conta.data_emissao.strftime("%d/%m/%Y"),
            "data_vencimento": conta.data_vencimento.strftime("%d/%m/%Y"),
            "cliente": {
                "id": conta.cliente.id,
                "nome": conta.cliente.nome,
                "documento": conta.cliente.documento or "",
            },
            # ---- SAÍDA ATUAL (NÃO ALTERADA) ----
            "pagamentos_conta": [
                {
                    "id": p.id,
                    "valor_pago": float(p.valor_pago),
                    "forma_pagamento": p.forma_pagamento.value,
                    "data_pagamento": p.data_pagamento.strftime("%d/%m/%Y"),
                    "observacoes": p.observacoes or "",
                    "caixa_id": p.caixa_id,
                }
                for p in conta.pagamentos
            ],
            # ---- NOVO RETORNO (SEM IMPACTAR O ANTERIOR) ----
            "pagamentos_efetuados": [
                {
                    "id": p.id,
                    "valor_pago": float(p.valor_pago),
                    "forma_pagamento": p.forma_pagamento.value,
                    "data_pagamento": p.data_pagamento.strftime("%d/%m/%Y %H:%M"),
                    "caixa_id": p.caixa_id,
                }
                for p in pagamento_efetuados
            ],
            # ---- NOTA FISCAL COMPLETA ----
            "nota_fiscal": nota_json,
            # ---- CAIXAS ----
            "caixas": caixas_json,
        }
    )


@admin_bp.route("/contas-receber/<int:id>/pdf", methods=["GET"])
@login_required
@admin_required
def gerar_pdf_conta_receber(id):
    conta = ContaReceber.query.get_or_404(id)

    # Configuração para bobina 80mm
    bobina_width = 226
    bobina_height = 3000

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(bobina_width, bobina_height),
        leftMargin=5,
        rightMargin=5,
        topMargin=-6,
        bottomMargin=5,
    )
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        name="Header",
        parent=styles["Heading1"],
        fontSize=14,
        leading=14,
        alignment=1,
        fontName="Helvetica-Bold",
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        name="Subtitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=12,
        alignment=1,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        name="Normal",
        parent=styles["Normal"],
        fontSize=10,
        leading=10,
        alignment=0,
        fontName="Helvetica",
    )
    valor_style = ParagraphStyle(
        name="Valor", parent=normal_style, alignment=2, fontName="Helvetica-Bold"
    )
    linha_style = ParagraphStyle(
        name="Linha", parent=normal_style, alignment=1, textColor=colors.black
    )

    def moeda_br(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def linha_separadora():
        return Paragraph("=" * 34, linha_style)

    # Função para criar linha alinhada com tabela invisível
    def linha_dupla(label, valor):
        from reportlab.platypus import Table, TableStyle

        tabela = Table(
            [[Paragraph(label, normal_style), Paragraph(valor, valor_style)]],
            colWidths=[120, 80],
        )
        tabela.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                    ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return tabela

    # Logo (se disponível)
    from flask import current_app
    import os
    from PIL import Image as PILImage
    from reportlab.platypus import Image, Spacer

    logo_path = os.path.join(current_app.root_path, "static", "assets", "logo.jpeg")
    if os.path.exists(logo_path):
        try:
            with PILImage.open(logo_path) as img:
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
            logo_width = 250
            logo_height = logo_width / aspect_ratio
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(0, 6))
        except Exception as e:
            logger.error(f"Erro ao carregar a logo: {e}", exc_info=True)

    # Cabeçalho
    elements.append(Paragraph("CONTA A RECEBER", header_style))
    elements.append(linha_separadora())
    elements.append(Spacer(1, 6))

    # Informações da conta
    elements.append(linha_dupla("Nº Documento:", str(conta.id)))
    elements.append(linha_dupla("Emissão:", conta.data_emissao.strftime("%d/%m/%Y")))
    elements.append(
        linha_dupla("Vencimento:", conta.data_vencimento.strftime("%d/%m/%Y"))
    )

    # Status
    status_text = ""
    if conta.status == StatusPagamento.quitado:
        status_text = "QUITADO"
    elif conta.status == StatusPagamento.parcial:
        status_text = "PAGAMENTO PARCIAL"
    else:
        hoje = datetime.now().date()
        if isinstance(conta.data_vencimento, datetime):
            vencimento = conta.data_vencimento.date()
        else:
            vencimento = conta.data_vencimento

        if vencimento < hoje:
            status_text = "VENCIDO"
        else:
            status_text = "PENDENTE"

    elements.append(linha_dupla("Status:", status_text))
    elements.append(Spacer(1, 6))

    # Informações do cliente
    elements.append(linha_separadora())
    elements.append(Paragraph("CLIENTE", subtitle_style))
    elements.append(Spacer(1, 4))
    elements.append(linha_separadora())

    elements.append(Paragraph(conta.cliente.nome, normal_style))
    if conta.cliente.documento:
        elements.append(
            Paragraph(f"Documento: {conta.cliente.documento}", normal_style)
        )

    elements.append(Spacer(1, 6))

    # Descrição (se houver)
    if conta.descricao:
        elements.append(linha_separadora())
        elements.append(Paragraph("DESCRIÇÃO", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())

        # Quebra de linha para descrição longa
        desc_lines = []
        words = conta.descricao.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if len(test_line) < 35:  # Aproximadamente a largura da bobina
                line = test_line
            else:
                desc_lines.append(line)
                line = word + " "
        if line:
            desc_lines.append(line)

        for line in desc_lines:
            elements.append(Paragraph(line, normal_style))

        elements.append(Spacer(1, 6))

    # Produtos da nota fiscal (se houver)
    if conta.nota_fiscal and conta.nota_fiscal.itens:
        elements.append(linha_separadora())
        elements.append(Paragraph("PRODUTOS DA NOTA FISCAL", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())

        # Cabeçalho da tabela de produtos
        from reportlab.platypus import Table, TableStyle

        data = [["Produto", "Qtd", "Valor Unit.", "Total"]]

        for item in conta.nota_fiscal.itens:
            # Formata quantidade com 3 casas decimais
            quantidade_str = f"{float(item.quantidade):.2f}"

            # Quebra o nome do produto em múltiplas linhas se for muito longo
            nome_produto = item.produto.nome
            if len(nome_produto) > 20:
                nome_lines = []
                words = nome_produto.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if len(test_line) < 20:
                        line = test_line
                    else:
                        nome_lines.append(line)
                        line = word + " "
                if line:
                    nome_lines.append(line)
                nome_cell = []
                for line in nome_lines:
                    nome_cell.append(Paragraph(line, normal_style))
            else:
                nome_cell = Paragraph(nome_produto, normal_style)

            data.append(
                [
                    nome_cell,
                    quantidade_str,
                    moeda_br(item.valor_unitario),
                    moeda_br(item.valor_total),
                ]
            )

        # Cria tabela
        tabela = Table(data, colWidths=[100, 30, 45, 45])
        tabela.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("ALIGN", (2, 0), (3, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        elements.append(tabela)
        elements.append(Spacer(1, 6))

        # Total da nota fiscal
        if conta.nota_fiscal:
            elements.append(
                linha_dupla("Total Nota:", moeda_br(conta.nota_fiscal.valor_total))
            )
            if conta.nota_fiscal.valor_desconto > 0:
                elements.append(
                    linha_dupla("Desconto:", moeda_br(conta.nota_fiscal.valor_desconto))
                )
            elements.append(Spacer(1, 6))

    # Valores
    elements.append(linha_separadora())
    elements.append(Paragraph("VALORES", subtitle_style))
    elements.append(Spacer(1, 4))
    elements.append(linha_separadora())

    elements.append(linha_dupla("Valor Original:", moeda_br(conta.valor_original)))
    elements.append(linha_dupla("Valor Pendente:", moeda_br(conta.valor_aberto)))
    elements.append(Spacer(1, 6))

    # Pagamentos realizados (se houver)
    if conta.pagamentos:
        elements.append(linha_separadora())
        elements.append(Paragraph("PAGAMENTOS REALIZADOS", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(linha_separadora())

        # Cabeçalho da tabela de pagamentos
        from reportlab.platypus import Table, TableStyle

        data = [["Data", "Valor", "Forma"]]

        for pagamento in conta.pagamentos:
            # Formata data
            if isinstance(pagamento.data_pagamento, datetime):
                data_pagamento_str = pagamento.data_pagamento.strftime("%d/%m/%Y")
            else:
                data_pagamento_str = pagamento.data_pagamento.strftime("%d/%m/%Y")

            # Formata forma de pagamento
            forma_pagamento = pagamento.forma_pagamento.value
            if forma_pagamento == "dinheiro":
                forma_abrev = "DIN"
            elif "pix" in forma_pagamento:
                forma_abrev = "PIX"
            elif "cartao_credito" in forma_pagamento:
                forma_abrev = "CC"
            elif "cartao_debito" in forma_pagamento:
                forma_abrev = "CD"
            else:
                forma_abrev = forma_pagamento[:3].upper()

            data.append(
                [data_pagamento_str, moeda_br(pagamento.valor_pago), forma_abrev]
            )

        # Cria tabela
        tabela = Table(data, colWidths=[60, 70, 40])
        tabela.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(tabela)
        elements.append(Spacer(1, 6))

    # Data de emissão do relatório
    elements.append(Spacer(1, 10))
    elements.append(linha_separadora())
    elements.append(
        Paragraph(
            f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style
        )
    )

    # Construir o PDF
    doc.build(elements)
    buffer.seek(0)

    # Criar resposta
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=conta_receber_{conta.id}.pdf"
    )

    return response


@admin_bp.route("/contas-receber/<int:id>/pagar", methods=["POST"])
@login_required
@admin_required
def pagar_conta_receber(id):
    conta = ContaReceber.query.get_or_404(id)
    data = request.get_json()

    try:
        # Validação do valor pago
        valor_pago = Decimal(str(data.get("valor_pago", 0)))
        if valor_pago <= 0:
            logger.warning(f"Valor de pagamento inválido: {valor_pago}")
            return jsonify({"error": "Valor deve ser positivo"}), 400
        if valor_pago > conta.valor_aberto:
            logger.warning(
                f"Valor de pagamento excede o valor em aberto: {valor_pago} > {conta.valor_aberto}"
            )
            return jsonify({"error": "Valor excede o valor em aberto"}), 400

        # Forma de pagamento
        forma_pagamento_str = data.get("forma_pagamento")
        if not forma_pagamento_str:
            logger.warning("Forma de pagamento não informada")
            return jsonify({"error": "Forma de pagamento não informada"}), 400
        try:
            forma_pagamento = FormaPagamento[forma_pagamento_str]
        except KeyError:
            logger.warning(f"Forma de pagamento inválida: {forma_pagamento_str}")
            return (
                jsonify(
                    {"error": f"Forma de pagamento inválida: {forma_pagamento_str}"}
                ),
                400,
            )

        # Caixa
        caixa_id = data.get("caixa_id")
        if caixa_id is not None:
            try:
                caixa_id = int(caixa_id)
                if not Caixa.query.get(caixa_id):
                    logger.warning(f"Caixa não encontrado: {caixa_id}")
                    return jsonify({"error": "Caixa não encontrado"}), 400
            except ValueError:
                logger.warning(f"ID do caixa inválido: {caixa_id}")
                return jsonify({"error": "ID do caixa inválido"}), 400
        else:
            caixa = (
                Caixa.query.filter_by(
                    operador_id=current_user.id, status=StatusCaixa.aberto
                )
                .order_by(Caixa.data_abertura.desc())
                .first()
            )
            if caixa:
                caixa_id = caixa.id
            else:
                logger.warning(
                    f"Nenhum caixa aberto encontrado para o usuário {current_user.nome}"
                )
                return (
                    jsonify({"error": "Nenhum caixa aberto encontrado para o usuário"}),
                    400,
                )

        # Observações
        observacoes = data.get("observacoes", "")

        # SEMPRE usa a data e hora atuais, ignorando qualquer entrada do frontend
        data_pagamento = datetime.now()

        # REGISTRAR PAGAMENTO
        pagamento = conta.registrar_pagamento(
            valor_pago=valor_pago,
            forma_pagamento=forma_pagamento,
            caixa_id=caixa_id,
            observacoes=observacoes,
            data_pagamento=data_pagamento,
        )

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "valor_aberto": float(conta.valor_aberto),
                "status": conta.status.value,
                "data_pagamento": data_pagamento.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),  # Retorna data e hora completas
            }
        )

    except Exception as e:
        logger.error(
            f"Erro ao processar pagamento da conta a receber {id}: {e}", exc_info=True
        )
        import traceback

        db.session.rollback()
        logger.error(f"Erro ao processar pagamento: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Erro interno ao processar pagamento: {str(e)}"}), 500


@admin_bp.route("/auditoria")
@login_required
@admin_required
def auditoria():
    # Obter lista de usuários para o filtro
    usuarios = (
        Usuario.query.with_entities(Usuario.id, Usuario.nome)
        .order_by(Usuario.nome)
        .all()
    )

    # Obter lista de tabelas disponíveis (pode ser hardcoded ou dinâmica)
    tabelas_disponiveis = [
        "clientes",
        "produtos",
        "usuarios",
        "transferencias_estoque",
        "descontos",
        "contas_receber",
        "financeiro",
        "pagamentos_contas_receber",
        "notas_fiscais",
        "pagamentos_nota_fiscal",
        "nota_fiscal_itens",
        "movimentacoes_estoque",
        "caixas",
    ]

    return render_template(
        "auditoria.html", usuarios=usuarios, tabelas_disponiveis=tabelas_disponiveis
    )


@admin_bp.route("/api/auditoria/logs")
@login_required
@admin_required
def api_auditoria_logs():
    # Obter parâmetros de filtro
    pagina = request.args.get("pagina", 1, type=int)
    por_pagina = request.args.get("por_pagina", 50, type=int)
    tabela = request.args.get("tabela", "")
    acao = request.args.get("acao", "")
    usuario_id = request.args.get("usuario_id", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    # Construir query base
    query = AuditLog.query

    # Aplicar filtros
    if tabela:
        query = query.filter(AuditLog.tabela.ilike(f"%{tabela}%"))
    if acao:
        query = query.filter(AuditLog.acao == acao)
    if usuario_id:
        query = query.filter(AuditLog.usuario_id == usuario_id)
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(AuditLog.criado_em >= data_inicio_dt)
        except ValueError:
            pass
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AuditLog.criado_em < data_fim_dt)
        except ValueError:
            pass

    # Ordenar e paginar
    logs = query.order_by(AuditLog.criado_em.desc()).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )

    # Formatar resposta
    logs_data = []
    for log in logs.items:
        logs_data.append(
            {
                "id": log.id,
                "tabela": log.tabela,
                "registro_id": log.registro_id,
                "usuario_id": log.usuario_id,
                "usuario_nome": log.usuario.nome if log.usuario else "N/A",
                "acao": log.acao,
                "antes": log.antes,
                "depois": log.depois,
                "criado_em": log.criado_em.isoformat(),
                "diferencas": (
                    calcular_diferencas(log.antes, log.depois)
                    if log.antes and log.depois
                    else []
                ),
            }
        )

    return jsonify(
        {
            "logs": logs_data,
            "total": logs.total,
            "paginas": logs.pages,
            "pagina_atual": pagina,
        }
    )


@admin_bp.route("/produtos/unidade")
@login_required
@admin_required
def listar_produtos_por_unidade():
    unidade = request.args.get("unidade")

    if not unidade:
        return "Unidade de medida não informada", 400

    produtos = buscar_produtos_por_unidade(unidade)

    return render_template("produtos_unidade.html", produtos=produtos, unidade=unidade)


@admin_bp.route("/produtos/unidade/pdf")
@login_required
@admin_required
def baixar_pdf_produtos():
    try:
        unidade = request.args.get("unidade")
        if not unidade:
            return "Unidade não informada", 400

        produtos = buscar_produtos_por_unidade(unidade)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=10 * mm,
            bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # -------------------- Cabeçalho --------------------
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
        elements.append(Paragraph(f"📦 Produtos da Unidade: {unidade}", header_style))
        elements.append(Spacer(1, 8))
        elements.append(
            Table(
                [["" * 80]],
                colWidths=[170 * mm],
                style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.black)],
            )
        )
        elements.append(Spacer(1, 12))

        # -------------------- Tabela --------------------
        table_data = [
            [
                Paragraph("Nome", styles["Normal"]),
                Paragraph("Estoque Loja", styles["Normal"]),
                Paragraph("Estoque Fábrica", styles["Normal"]),
                Paragraph("Estoque Depósito", styles["Normal"]),
                Paragraph("Preço de Venda", styles["Normal"]),
            ]
        ]

        # Estilo para células
        cell_style = ParagraphStyle(
            "Cell", fontSize=8, leading=10, alignment=TA_CENTER, wordWrap="CJK"
        )
        cell_left = ParagraphStyle("CellLeft", parent=cell_style, alignment=TA_LEFT)

        for p in produtos:
            valor_unitario = f"R$ {p.valor_unitario:,.2f}" if p.valor_unitario else "-"
            table_data.append(
                [
                    Paragraph(p.nome, cell_left),
                    Paragraph(f"{p.estoque_loja:,.2f}", cell_style),
                    Paragraph(f"{p.estoque_fabrica:,.2f}", cell_style),
                    Paragraph(f"{p.estoque_deposito:,.2f}", cell_style),
                    Paragraph(valor_unitario, cell_style),
                ]
            )

        col_widths = [60 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm]

        produto_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = TableStyle(
            [
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )

        # Linhas zebradas
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add("BACKGROUND", (0, i), (-1, i), colors.whitesmoke)

        produto_table.setStyle(table_style)
        elements.append(produto_table)

        # -------------------- Rodapé --------------------
        elements.append(Spacer(1, 15))
        rodape = datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M")
        elements.append(
            Paragraph(
                rodape,
                ParagraphStyle(
                    "Rodape", fontSize=8, alignment=TA_RIGHT, textColor=colors.grey
                ),
            )
        )

        doc.build(elements)

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"produtos_{unidade}.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        logger.error(
            f"Erro ao gerar PDF de produtos por unidade: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/financeiro/historico", methods=["GET"])
@login_required
@admin_required
def historico_financeiro():
    tipo = request.args.get("tipo")
    data_str = request.args.get("data")
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    operador_id = request.args.get("operador_id", type=int)
    incluir_outros = request.args.get("incluir_outros", "false").lower() == "true"

    if not tipo:
        return "Tipo de movimentação não informado", 400

    try:
        tipo_movimentacao = TipoMovimentacao(tipo)
    except ValueError:
        return "Tipo de movimentação inválido", 400

    start_date = None
    end_date = None
    mes_ano_display = None

    if start_str and end_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            mes_ano_display = start_date.strftime("%m/%Y")
        except Exception as e:
            return f"Datas de filtro inválidas. Use YYYY-MM-DD. Erro: {str(e)}", 400

    elif data_str:
        try:
            mes, ano = map(int, data_str.split("-"))
            start_date = datetime(ano, mes, 1)
            if mes == 12:
                end_date = datetime(ano, 12, 31)
            else:
                end_date = datetime(ano, mes + 1, 1) - timedelta(days=1)
            end_date = end_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            mes_ano_display = data_str.replace("-", "/")
        except Exception as e:
            return f"Data inválida. Use MM-YYYY. Erro: {str(e)}", 400

    else:
        hoje = datetime.now()
        start_date = datetime(hoje.year, hoje.month, 1)
        if hoje.month == 12:
            end_date = datetime(hoje.year, 12, 31)
        else:
            end_date = datetime(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        mes_ano_display = hoje.strftime("%m/%Y")

    from app.models.entities import Usuario, TipoUsuario

    operadores = (
        Usuario.query.filter(Usuario.tipo == TipoUsuario.operador)
        .order_by(Usuario.nome)
        .all()
    )

    operador_selecionado = None
    if operador_id:
        operador_selecionado = Usuario.query.get(operador_id)

    historico_agrupado = buscar_historico_financeiro_agrupado(
        tipo_movimentacao,
        data=None,
        incluir_outros=incluir_outros,
        start_date=start_date,
        end_date=end_date,
        operador_id=operador_id,
    )

    return render_template(
        "financeiro_historico.html",
        tipo_movimentacao=tipo_movimentacao.value,
        historico=historico_agrupado,
        mes_ano=mes_ano_display,
        start_date=start_date.strftime("%Y-%m-%d") if start_date else "",
        end_date=end_date.strftime("%Y-%m-%d") if end_date else "",
        operadores=operadores,
        operador_id=operador_id,
        operador_selecionado=operador_selecionado,
    )


@admin_bp.route("/financeiro/historico/json", methods=["GET"])
@login_required
@admin_required
def historico_financeiro_json():
    tipo = request.args.get("tipo")
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    incluir_outros = request.args.get("incluir_outros", "false").lower() == "true"

    if not tipo:
        return jsonify({"error": "Tipo de movimentação não informado"}), 400

    try:
        tipo_movimentacao = TipoMovimentacao(tipo)
    except ValueError:
        return jsonify({"error": "Tipo de movimentação inválido"}), 400

    start_date = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None

    if end_str:
        # Ajusta o end_date para incluir o último segundo do dia
        end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
    else:
        end_date = None

    historico = buscar_historico_financeiro_agrupado(
        tipo_movimentacao,
        start_date=start_date,
        end_date=end_date,
        incluir_outros=incluir_outros,
    )

    # Serializar para JSON
    def serialize(f):
        return {
            "id_financeiro": f["id_financeiro"],
            "categoria": f["categoria"],
            "valor_total_nota": float(f["valor_total_nota"]),
            "descricao": f["descricao"],
            "data": (
                f["data"].strftime("%d/%m/%Y %H:%M")
                if isinstance(f["data"], datetime)
                else f["data"]
            ),
            "cliente": f["cliente"],
            "caixa": f["caixa"],
            "nota_fiscal_id": f["nota_fiscal_id"],
            "pagamentos": [
                {
                    "forma_pagamento": (
                        p.forma_pagamento.value if p.forma_pagamento else "-"
                    ),
                    "valor": float(p.valor),
                }
                for p in f["pagamentos"]
            ],
        }

    return jsonify([serialize(f) for f in historico])


# ================= ROTA PDF CORRIGIDA =================
@admin_bp.route("/financeiro/historico/pdf")
@login_required
@admin_required
def historico_financeiro_pdf():
    try:
        tipo = request.args.get("tipo")
        data_str = request.args.get("data")
        start_date_str = request.args.get("start")
        end_date_str = request.args.get("end")

        if not tipo:
            abort(400, description="Tipo de movimentação não informado")

        try:
            tipo_movimentacao = TipoMovimentacao(tipo)
        except ValueError:
            abort(400, description="Tipo de movimentação inválido")

        data = datetime.now(ZoneInfo("America/Sao_Paulo"))
        if data_str:
            mes, ano = map(int, data_str.split("-"))
            data = datetime(ano, mes, 1)

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            if end_date_str
            else None
        )

        # -------------------- BUSCAR CAIXAS --------------------
        query_caixas = Caixa.query
        if start_date:
            query_caixas = query_caixas.filter(Caixa.data_abertura >= start_date)
        if end_date:
            query_caixas = query_caixas.filter(Caixa.data_abertura <= end_date)
        caixas = query_caixas.order_by(Caixa.data_abertura.desc()).all()

        # -------------------- CÁLCULOS --------------------
        total_geral_entradas = 0
        total_geral_saidas = 0
        total_geral_estornos = 0
        total_geral_vendas = 0
        total_geral_contas_recebidas = 0
        total_pagamentos_consolidado = {}

        for caixa in caixas:
            pagamentos_notas = (
                db.session.query(
                    PagamentoNotaFiscal.forma_pagamento,
                    func.sum(PagamentoNotaFiscal.valor).label("total"),
                )
                .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
                .filter(
                    NotaFiscal.caixa_id == caixa.id,
                    NotaFiscal.status == StatusNota.emitida,
                )
                .group_by(PagamentoNotaFiscal.forma_pagamento)
                .all()
            )

            pagamentos_contas = []
            if tipo_movimentacao == TipoMovimentacao.entrada:
                pagamentos_contas = (
                    db.session.query(
                        PagamentoContaReceber.forma_pagamento,
                        func.sum(PagamentoContaReceber.valor_pago).label("total"),
                    )
                    .filter(PagamentoContaReceber.caixa_id == caixa.id)
                    .group_by(PagamentoContaReceber.forma_pagamento)
                    .all()
                )

            caixa_vendas = 0.0
            for forma, total in pagamentos_notas:
                valor = float(total) if total else 0.0
                if tipo_movimentacao == TipoMovimentacao.entrada:
                    total_pagamentos_consolidado[forma.value] = (
                        total_pagamentos_consolidado.get(forma.value, 0) + valor
                    )
                caixa_vendas += valor
            total_geral_vendas += caixa_vendas

            caixa_contas_recebidas = 0.0
            if tipo_movimentacao == TipoMovimentacao.entrada:
                for forma, total in pagamentos_contas:
                    valor = float(total) if total else 0.0
                    total_pagamentos_consolidado[forma.value] = (
                        total_pagamentos_consolidado.get(forma.value, 0) + valor
                    )
                    caixa_contas_recebidas += valor
                total_geral_contas_recebidas += caixa_contas_recebidas

            caixa_entradas_bruto = caixa_vendas + caixa_contas_recebidas

            estornos = 0.0
            if tipo_movimentacao == TipoMovimentacao.entrada:
                estornos = (
                    db.session.query(func.sum(Financeiro.valor))
                    .filter(
                        Financeiro.caixa_id == caixa.id,
                        Financeiro.tipo == TipoMovimentacao.saida_estorno,
                    )
                    .scalar()
                    or 0.0
                )

            estornos_valor = float(estornos)
            total_geral_estornos += estornos_valor

            if tipo_movimentacao == TipoMovimentacao.entrada:
                entradas_liquidas = caixa_entradas_bruto - estornos_valor
                total_geral_entradas += entradas_liquidas

            if tipo_movimentacao == TipoMovimentacao.saida:
                caixa_saidas = (
                    db.session.query(func.sum(Financeiro.valor))
                    .filter(
                        Financeiro.caixa_id == caixa.id,
                        Financeiro.tipo == TipoMovimentacao.saida,
                        Financeiro.categoria == CategoriaFinanceira.despesa,
                    )
                    .scalar()
                    or 0.0
                )
                total_geral_saidas += float(caixa_saidas)

        # -------------------- HISTÓRICO --------------------
        financeiros = buscar_historico_financeiro_agrupado(
            tipo_movimentacao,
            data=data,
            start_date=start_date,
            end_date=end_date,
            incluir_outros=False,
        )

        pagamentos_contas = []
        if tipo_movimentacao == TipoMovimentacao.entrada:
            query_pagamentos_contas = PagamentoContaReceber.query.join(
                ContaReceber, PagamentoContaReceber.conta_id == ContaReceber.id
            ).filter(
                ContaReceber.status.in_(
                    [StatusPagamento.parcial, StatusPagamento.quitado]
                )
            )
            if start_date:
                query_pagamentos_contas = query_pagamentos_contas.filter(
                    PagamentoContaReceber.data_pagamento >= start_date
                )
            if end_date:
                query_pagamentos_contas = query_pagamentos_contas.filter(
                    PagamentoContaReceber.data_pagamento <= end_date
                )
            pagamentos_contas = query_pagamentos_contas.all()

            # REMOVER DUPLICADOS dos pagamentos de contas
            pagamentos_contas_unicos = []
            ids_pagamentos_vistos = set()

            for pagamento in pagamentos_contas:
                if pagamento.id not in ids_pagamentos_vistos:
                    pagamentos_contas_unicos.append(pagamento)
                    ids_pagamentos_vistos.add(pagamento.id)

        # -------------------- PDF --------------------
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=10 * mm,
            bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading1"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
        )

        if start_date and end_date:
            periodo_texto = (
                f"{start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}"
            )
        elif start_date:
            periodo_texto = f"A partir de {start_date.strftime('%d/%m/%Y')}"
        elif end_date:
            periodo_texto = f"Até {end_date.strftime('%d/%m/%Y')}"
        else:
            periodo_texto = data.strftime("%m/%Y")

        elements.append(
            Paragraph(
                f"💰 Histórico Financeiro - {tipo_movimentacao.value} ({periodo_texto})",
                header_style,
            )
        )
        elements.append(Spacer(1, 8))

        # -------------------- TABELA DETALHADA --------------------
        cell_style_center = ParagraphStyle(
            "CellCenter", fontSize=8, leading=10, alignment=TA_CENTER, wordWrap="CJK"
        )
        cell_style_left = ParagraphStyle(
            "CellLeft", fontSize=8, leading=10, alignment=TA_LEFT, wordWrap="CJK"
        )

        table_data = [
            [
                Paragraph("ID", cell_style_center),
                Paragraph("Categoria", cell_style_center),
                Paragraph("Valor", cell_style_center),
                Paragraph("Descrição", cell_style_center),
                Paragraph("Data", cell_style_center),
                Paragraph("Cliente", cell_style_center),
                Paragraph("Caixa", cell_style_center),
                Paragraph("Pagamentos", cell_style_center),
            ]
        ]

        for f in financeiros:
            pagamentos_texto = ""
            valor_total = f["valor_total_nota"]  # Usar o valor total da nota fiscal

            if f["nota_fiscal_id"] and tipo_movimentacao == TipoMovimentacao.entrada:
                for p in f["pagamentos"]:
                    forma = (
                        p.forma_pagamento.value
                        if hasattr(p, "forma_pagamento") and p.forma_pagamento
                        else "-"
                    )
                    pagamentos_texto += f"{forma}: R$ {p.valor:.2f}\n"

            table_data.append(
                [
                    Paragraph(str(f["id_financeiro"]), cell_style_center),
                    Paragraph(f["categoria"], cell_style_center),
                    Paragraph(
                        f"R$ {valor_total:.2f}", cell_style_center
                    ),  # Mostrar valor total
                    Paragraph(f["descricao"], cell_style_left),
                    Paragraph(f["data"].strftime("%d/%m/%Y %H:%M"), cell_style_center),
                    Paragraph(f["cliente"], cell_style_center),
                    Paragraph(str(f["caixa"]), cell_style_center),
                    Paragraph(pagamentos_texto.strip() or "-", cell_style_left),
                ]
            )

        if tipo_movimentacao == TipoMovimentacao.entrada:
            for pagamento in pagamentos_contas_unicos:
                descricao = f"Pagamento conta #{pagamento.conta_id}"
                if pagamento.conta and pagamento.conta.descricao:
                    descricao += f" - {pagamento.conta.descricao}"
                pagamentos_texto = (
                    f"{pagamento.forma_pagamento.value}: R$ {pagamento.valor_pago:.2f}"
                )
                table_data.append(
                    [
                        Paragraph(f"CR-{pagamento.id}", cell_style_center),
                        Paragraph("Recebimento", cell_style_center),
                        Paragraph(f"R$ {pagamento.valor_pago:.2f}", cell_style_center),
                        Paragraph(descricao, cell_style_left),
                        Paragraph(
                            pagamento.data_pagamento.strftime("%d/%m/%Y %H:%M"),
                            cell_style_center,
                        ),
                        Paragraph(
                            (
                                pagamento.conta.cliente.nome
                                if pagamento.conta and pagamento.conta.cliente
                                else "-"
                            ),
                            cell_style_center,
                        ),
                        Paragraph(
                            str(pagamento.caixa_id) if pagamento.caixa_id else "-",
                            cell_style_center,
                        ),
                        Paragraph(pagamentos_texto, cell_style_left),
                    ]
                )

        if len(table_data) > 1:
            col_widths = [
                20 * mm,
                25 * mm,
                25 * mm,
                50 * mm,
                25 * mm,
                25 * mm,
                20 * mm,
                50 * mm,
            ]
            t = Table(table_data, colWidths=col_widths, hAlign="CENTER", repeatRows=1)
            t.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONT", (0, 1), (-1, -1), "Helvetica", 7),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ]
                )
            )
            elements.append(t)
            elements.append(Spacer(1, 10))

        # ----------------- TOTAIS -----------------
        import locale

        locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

        if (
            tipo_movimentacao == TipoMovimentacao.entrada
            and total_pagamentos_consolidado
        ):
            totals_pagamentos_data = [
                [
                    Paragraph("<b>Totais por forma de pagamento</b>", styles["Normal"]),
                    "",
                ]
            ]
            formas_ordenadas = sorted(
                total_pagamentos_consolidado.items(), key=lambda x: x[1], reverse=True
            )
            for forma, valor in formas_ordenadas:
                if valor > 0:
                    totals_pagamentos_data.append(
                        [
                            Paragraph(
                                forma.replace("_", " ").capitalize(), styles["Normal"]
                            ),
                            Paragraph(
                                locale.format_string("R$ %.2f", valor, grouping=True),
                                styles["Normal"],
                            ),
                        ]
                    )
            soma_formas = sum(valor for _, valor in formas_ordenadas if valor > 0)
            totals_pagamentos_data.append(
                [
                    Paragraph("<b>Soma das formas</b>", styles["Normal"]),
                    Paragraph(
                        f"<b>{locale.format_string('R$ %.2f', soma_formas, grouping=True)}</b>",
                        styles["Normal"],
                    ),
                ]
            )
            totals_pagamentos_data.append(
                [
                    Paragraph("<b>Total Entradas Líquidas</b>", styles["Normal"]),
                    Paragraph(
                        f"<b>{locale.format_string('R$ %.2f', total_geral_entradas, grouping=True)}</b>",
                        styles["Normal"],
                    ),
                ]
            )
            totals_pagamentos_data.append(
                [
                    Paragraph(
                        "<font size=8 color='grey'>Observação:</font>", styles["Normal"]
                    ),
                    Paragraph(
                        f"<font size=8 color='grey'>Valor total de Estornos R$ {total_geral_estornos:,.2f} já deduzido das Entradas Líquidas.</font>",
                        styles["Normal"],
                    ),
                ]
            )

            totals_pagamentos_table = Table(
                totals_pagamentos_data, colWidths=[80 * mm, 40 * mm], hAlign="LEFT"
            )
            totals_pagamentos_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LINEABOVE", (0, -2), (-1, -2), 0.7, colors.black),
                        ("BACKGROUND", (0, -2), (-1, -2), colors.lightgrey),
                        ("FONT", (0, -2), (-1, -2), "Helvetica-Bold", 9),
                    ]
                )
            )
            elements.append(totals_pagamentos_table)

        if tipo_movimentacao == TipoMovimentacao.saida:
            totals_data = [
                [
                    "TOTAL DE DESPESAS",
                    locale.format_string("R$ %.2f", total_geral_saidas, grouping=True),
                ]
            ]
            totals_table = Table(
                totals_data, colWidths=[100 * mm, 60 * mm], hAlign="LEFT"
            )
            totals_table.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, -1), "Helvetica-Bold", 9),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
                    ]
                )
            )
            elements.append(totals_table)

        elements.append(
            Paragraph(
                datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M"),
                ParagraphStyle(
                    "Rodape", fontSize=8, alignment=TA_RIGHT, textColor=colors.grey
                ),
            )
        )

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"historico_financeiro_{tipo}_{data.strftime('%m_%Y')}.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        logger.error(
            f"Erro ao gerar PDF do histórico financeiro: {str(e)}", exc_info=True
        )
        abort(500, description=str(e))


# ============ ROTAS DAS CONTAS DOS USUÁRIOS ==============
@admin_bp.route("/dashboard/contas")
@login_required
@admin_required
def dashboard_contas():
    logger.info(f"Acessando dashboard Contas - Usuário: {current_user.nome}")
    return render_template(
        "contas_usuario.html",
        nome_usuario=current_user.nome,
        tipo_usuario=current_user.tipo.value,
    )


@admin_bp.route("/conta/criar/<int:usuario_id>", methods=["POST"])
@login_required
@admin_required
def criar_conta_usuario(usuario_id):
    try:
        # Verificar se o usuário existe
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Verificar se o usuário já possui conta
        if usuario.conta:
            return jsonify({"error": "Usuário já possui uma conta"}), 400

        # Criar a conta
        conta = Conta(usuario_id=usuario_id)
        db.session.add(conta)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Conta criada com sucesso",
                    "conta": conta.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao criar conta: {str(e)}"}), 500


@admin_bp.route("/conta/transferir", methods=["POST"])
@login_required
@admin_required
def transferir_entre_contas():
    try:
        data = request.get_json()

        # Validar dados obrigatórios
        required_fields = [
            "conta_origem_id",
            "conta_destino_id",
            "forma_pagamento",
            "valor",
        ]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Campo obrigatório faltando: {field}"}), 400

        conta_origem_id = data["conta_origem_id"]
        conta_destino_id = data["conta_destino_id"]
        forma_pagamento = data["forma_pagamento"]
        valor = Decimal(str(data["valor"]))
        descricao = data["descricao"]
        usuario_id = current_user.id

        if valor <= 0:
            return jsonify({"error": "O valor da transferência deve ser positivo"}), 400

        conta_origem = Conta.query.get(conta_origem_id)
        conta_destino = Conta.query.get(conta_destino_id)

        if not conta_origem:
            return jsonify({"error": "Conta de origem não encontrada"}), 404
        if not conta_destino:
            return jsonify({"error": "Conta de destino não encontrada"}), 404
        if conta_origem_id == conta_destino_id:
            return (
                jsonify({"error": "Não é possível transferir para a mesma conta"}),
                400,
            )

        try:
            forma_pagamento_enum = FormaPagamento(forma_pagamento)
        except ValueError:
            return jsonify({"error": "Forma de pagamento inválida"}), 400

        # Verificar saldo da forma de pagamento na origem
        saldo_fp_origem = conta_origem.get_saldo_forma_pagamento(forma_pagamento_enum)
        if saldo_fp_origem < valor:
            return (
                jsonify(
                    {
                        "error": f"Saldo insuficiente em {forma_pagamento_enum.value}. "
                        f"Saldo atual: R$ {saldo_fp_origem:.2f}, Valor solicitado: R$ {valor:.2f}"
                    }
                ),
                400,
            )

        with db.session.begin_nested():
            conta_destino_nome = conta_destino.get_usuario_nome()
            conta_origem_nome = conta_origem.get_usuario_nome()

            # Descrições completas
            descricao_saida = (
                f"{descricao} | Conta destino: {conta_destino_nome}"
                if descricao
                else f"Conta destino: {conta_destino_nome}"
            )
            descricao_entrada = (
                f"{descricao} | Conta origem: {conta_origem_nome}"
                if descricao
                else f"Conta origem: {conta_origem_nome}"
            )

            # Movimentação de saída (origem)
            movimentacao_saida = MovimentacaoConta(
                conta_id=conta_origem_id,
                tipo=TipoMovimentacao.transferencia,
                forma_pagamento=forma_pagamento_enum,
                valor=valor,
                descricao=descricao_saida,
                usuario_id=usuario_id,
            )
            db.session.add(movimentacao_saida)

            # Movimentação de entrada (destino)
            movimentacao_entrada = MovimentacaoConta(
                conta_id=conta_destino_id,
                tipo=TipoMovimentacao.entrada,
                forma_pagamento=forma_pagamento_enum,
                valor=valor,
                descricao=descricao_entrada,
                usuario_id=usuario_id,
            )
            db.session.add(movimentacao_entrada)

            # Atualizar saldo total
            conta_origem.saldo_total -= valor
            conta_destino.saldo_total += valor

            # Atualizar saldo por forma de pagamento - ORIGEM
            saldo_fp_origem_obj = next(
                (
                    s
                    for s in conta_origem.saldos_forma_pagamento
                    if s.forma_pagamento == forma_pagamento_enum
                ),
                None,
            )
            if not saldo_fp_origem_obj:
                saldo_fp_origem_obj = SaldoFormaPagamento(
                    conta_id=conta_origem.id,
                    forma_pagamento=forma_pagamento_enum,
                    saldo=Decimal("0.00"),
                )
                db.session.add(saldo_fp_origem_obj)

            saldo_fp_origem_obj.saldo -= valor

            # Atualizar saldo por forma de pagamento - DESTINO
            saldo_fp_destino_obj = next(
                (
                    s
                    for s in conta_destino.saldos_forma_pagamento
                    if s.forma_pagamento == forma_pagamento_enum
                ),
                None,
            )
            if not saldo_fp_destino_obj:
                saldo_fp_destino_obj = SaldoFormaPagamento(
                    conta_id=conta_destino.id,
                    forma_pagamento=forma_pagamento_enum,
                    saldo=Decimal("0.00"),
                )
                db.session.add(saldo_fp_destino_obj)

            saldo_fp_destino_obj.saldo += valor

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Transferência de R$ {valor:.2f} realizada com sucesso",
                    "transferencia": {
                        "conta_origem_id": conta_origem_id,
                        "conta_destino_id": conta_destino_id,
                        "forma_pagamento": forma_pagamento_enum.value,
                        "valor": float(valor),
                        "descricao": descricao,
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao realizar transferência: {str(e)}"}), 500


@admin_bp.route("/conta/entrada", methods=["POST"])
@login_required
@admin_required
def entrada_conta():
    try:
        data = request.get_json()

        conta_id = data.get("conta_id")
        forma_pagamento = data.get("forma_pagamento")
        valor = data.get("valor")
        descricao = data.get("descricao", "Entrada na conta")
        usuario_id = current_user.id

        # Validações
        if not all([conta_id, forma_pagamento, valor, usuario_id]):
            return jsonify({"success": False, "error": "Dados incompletos"}), 400

        if valor <= 0:
            return jsonify({"success": False, "error": "Valor deve ser positivo"}), 400

        # Buscar conta
        conta = Conta.query.get(conta_id)
        if not conta:
            return jsonify({"success": False, "error": "Conta não encontrada"}), 404

        # Converter valor para Decimal
        valor_decimal = Decimal(str(valor))

        # Criar movimentação de entrada
        movimentacao = MovimentacaoConta(
            conta_id=conta_id,
            tipo=TipoMovimentacao.entrada,
            forma_pagamento=FormaPagamento(forma_pagamento),
            valor=valor_decimal,
            descricao=descricao,
            data=datetime.now(),
            usuario_id=usuario_id,
        )

        # Atualizar saldo total da conta
        conta.saldo_total += valor_decimal

        # Atualizar saldo específico da forma de pagamento
        saldo_forma = SaldoFormaPagamento.query.filter_by(
            conta_id=conta_id, forma_pagamento=FormaPagamento(forma_pagamento)
        ).first()

        if saldo_forma:
            saldo_forma.saldo += valor_decimal
            saldo_forma.atualizado_em = datetime.now()
        else:
            saldo_forma = SaldoFormaPagamento(
                conta_id=conta_id,
                forma_pagamento=FormaPagamento(forma_pagamento),
                saldo=valor_decimal,
            )
            db.session.add(saldo_forma)

        db.session.add(movimentacao)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Entrada registrada com sucesso",
                "novo_saldo": float(conta.saldo_total),
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/conta/saida", methods=["POST"])
@login_required
@admin_required
def saida_conta():
    try:
        data = request.get_json()

        conta_id = data.get("conta_id")
        forma_pagamento = data.get("forma_pagamento")
        valor = data.get("valor")
        descricao = data.get("descricao", "Saída da conta")
        usuario_id = current_user.id

        # Validações básicas
        if not all([conta_id, forma_pagamento, valor, usuario_id]):
            return jsonify({"success": False, "error": "Dados incompletos"}), 400

        valor_decimal = Decimal(str(valor))
        if valor_decimal <= 0:
            return jsonify({"success": False, "error": "Valor deve ser positivo"}), 400

        # Buscar conta
        conta = Conta.query.get(conta_id)
        if not conta:
            return jsonify({"success": False, "error": "Conta não encontrada"}), 404

        forma_pagamento_enum = FormaPagamento(forma_pagamento)

        # Buscar ou criar saldo por forma de pagamento
        saldo_forma = SaldoFormaPagamento.query.filter_by(
            conta_id=conta_id, forma_pagamento=forma_pagamento_enum
        ).first()

        if not saldo_forma:
            saldo_forma = SaldoFormaPagamento(
                conta_id=conta_id,
                forma_pagamento=forma_pagamento_enum,
                saldo=Decimal("0.00"),
                atualizado_em=datetime.now(),
            )
            db.session.add(saldo_forma)

        # Verificar saldo suficiente
        if saldo_forma.saldo < valor_decimal:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Saldo insuficiente em {forma_pagamento_enum.value}. "
                        f"Saldo atual: R$ {saldo_forma.saldo:.2f}",
                    }
                ),
                400,
            )

        # Criar movimentação de saída
        movimentacao = MovimentacaoConta(
            conta_id=conta_id,
            tipo=TipoMovimentacao.saida,
            forma_pagamento=forma_pagamento_enum,
            valor=valor_decimal,
            descricao=descricao,
            data=datetime.now(),
            usuario_id=usuario_id,
        )
        db.session.add(movimentacao)

        # Atualizar saldos
        conta.saldo_total -= valor_decimal
        saldo_forma.saldo -= valor_decimal
        saldo_forma.atualizado_em = datetime.now()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Saída registrada com sucesso",
                "novo_saldo_total": float(conta.saldo_total),
                "novo_saldo_forma": float(saldo_forma.saldo),
                "forma_pagamento": forma_pagamento_enum.value,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/conta/<int:conta_id>", methods=["GET"])
@login_required
@admin_required
def get_conta(conta_id):
    try:
        conta = Conta.query.get(conta_id)
        if not conta:
            return jsonify({"success": False, "error": "Conta não encontrada"}), 404

        return jsonify({"success": True, "conta": conta.to_dict()})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------
# Rotas para Dashboard de Contas
# --------------------
@admin_bp.route("/api/contas-usuario", methods=["GET"])
@login_required
@admin_required
def api_listar_contas_usuario():
    """Retorna lista de contas com saldos formatados para o dashboard"""
    try:
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        # Caso haja filtro por datas, filtra movimentações e recalcula saldos
        contas = Conta.query.filter_by(status=True).all()
        contas_data = []

        for conta in contas:
            # Filtro por data se fornecido
            movimentacoes_query = conta.movimentacoes
            if data_inicio:
                movimentacoes_query = [
                    m
                    for m in movimentacoes_query
                    if m.data >= datetime.fromisoformat(data_inicio)
                ]
            if data_fim:
                data_fim_dt = datetime.fromisoformat(data_fim)
                data_fim_dt = data_fim_dt.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                movimentacoes_query = [
                    m for m in movimentacoes_query if m.data <= data_fim_dt
                ]

            # Recalcula o saldo total e por forma de pagamento no intervalo
            saldos_por_forma_pagamento = {}
            total = 0.0

            for mov in movimentacoes_query:
                valor = float(mov.valor)
                if mov.tipo in ("saida", "transferencia"):
                    valor *= -1
                total += valor
                saldos_por_forma_pagamento[mov.forma_pagamento.value] = (
                    saldos_por_forma_pagamento.get(mov.forma_pagamento.value, 0.0)
                    + valor
                )

            conta_data = {
                "id": conta.id,
                "usuario_id": conta.usuario_id,
                "saldo_total_raw": total,
                "saldo_total": locale.currency(total, grouping=True),
                "saldos_por_forma_pagamento": {
                    k: locale.currency(v, grouping=True)
                    for k, v in saldos_por_forma_pagamento.items()
                },
                "atualizado_em": (
                    conta.atualizado_em.isoformat() if conta.atualizado_em else None
                ),
            }
            contas_data.append(conta_data)

        return jsonify({"success": True, "contas": contas_data})
    except Exception as e:
        logger.error(f"Erro ao listar contas para dashboard: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/contas-usuario/<int:conta_id>/movimentacoes", methods=["GET"])
@login_required
@admin_required
def api_listar_movimentacoes_conta_usuario(conta_id):
    try:
        conta = Conta.query.get(conta_id)
        if not conta:
            return jsonify({"success": False, "error": "Conta não encontrada"}), 404

        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        query = MovimentacaoConta.query.filter_by(conta_id=conta_id)

        if data_inicio:
            try:
                data_inicio_dt = datetime.fromisoformat(data_inicio)
                query = query.filter(MovimentacaoConta.data >= data_inicio_dt)
            except ValueError:
                return (
                    jsonify(
                        {"success": False, "error": "Formato de data início inválido"}
                    ),
                    400,
                )

        if data_fim:
            try:
                data_fim_dt = datetime.fromisoformat(data_fim)
                query = query.filter(MovimentacaoConta.data <= data_fim_dt)
            except ValueError:
                return (
                    jsonify(
                        {"success": False, "error": "Formato de data fim inválido"}
                    ),
                    400,
                )

        pagination = query.order_by(MovimentacaoConta.data.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        movimentacoes = pagination.items

        movimentacoes_data = [
            {
                "id": mov.id,
                "tipo": mov.tipo.value,
                "forma_pagamento": mov.forma_pagamento.value,
                "valor": locale.currency(float(mov.valor), grouping=True),
                "descricao": mov.descricao,
                "data": mov.data.isoformat() if mov.data else None,
                "usuario_id": mov.usuario_id,
                "caixa_id": mov.caixa_id,
            }
            for mov in movimentacoes
        ]

        return jsonify(
            {
                "success": True,
                "movimentacoes": movimentacoes_data,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            }
        )
    except Exception as e:
        logger.error(f"Erro ao listar movimentações da conta {conta_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/relatorios/movimentacoes-contas-usuario", methods=["GET"])
@login_required
@admin_required
def api_relatorio_movimentacoes():
    """Gera relatório de movimentações com filtros"""
    try:
        # Parâmetros de filtro
        conta_id = request.args.get("conta_id", type=int)
        usuario_id = request.args.get("usuario_id", type=int)
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        # Query base para movimentações
        query = db.session.query(
            Usuario.nome.label("usuario_nome"),
            MovimentacaoConta.conta_id,
            MovimentacaoConta.forma_pagamento,
            MovimentacaoConta.data,
            db.func.sum(
                db.case(
                    (
                        MovimentacaoConta.tipo == TipoMovimentacao.entrada,
                        MovimentacaoConta.valor,
                    ),
                    else_=0,
                )
            ).label("entradas"),
            db.func.sum(
                db.case(
                    (
                        MovimentacaoConta.tipo == TipoMovimentacao.saida,
                        MovimentacaoConta.valor,
                    ),
                    else_=0,
                )
            ).label("saidas"),
        ).join(Usuario, MovimentacaoConta.usuario_id == Usuario.id)

        # Aplicar filtros
        if conta_id:
            query = query.filter(MovimentacaoConta.conta_id == conta_id)
        if usuario_id:
            query = query.filter(MovimentacaoConta.usuario_id == usuario_id)
        if data_inicio:
            data_inicio_dt = datetime.fromisoformat(data_inicio)
            query = query.filter(MovimentacaoConta.data >= data_inicio_dt)
        if data_fim:
            data_fim_dt = datetime.fromisoformat(data_fim)
            query = query.filter(MovimentacaoConta.data <= data_fim_dt)

        resultados = (
            query.group_by(
                Usuario.nome,
                MovimentacaoConta.conta_id,
                MovimentacaoConta.forma_pagamento,
                MovimentacaoConta.data,
            )
            .order_by(MovimentacaoConta.data.desc())
            .all()
        )

        return jsonify(
            {
                "success": True,
                "dados": [
                    {
                        "usuario_nome": r.usuario_nome,
                        "conta_id": r.conta_id,
                        "forma_pagamento": r.forma_pagamento.value,
                        "entradas": float(r.entradas or 0),
                        "saidas": float(r.saidas or 0),
                        "data": r.data.isoformat() if r.data else None,
                    }
                    for r in resultados
                ],
            }
        )

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de movimentações: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/relatorios/movimentacoes-contas-usuario/pdf", methods=["POST"])
@login_required
@admin_required
def api_gerar_pdf_relatorio():
    """Gera relatório em PDF com todas as movimentações"""
    try:
        from flask import send_file
        import io
        import locale
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
        )
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from datetime import datetime

        # Configura formatação monetária brasileira
        try:
            locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_ALL, "")  # fallback

        def formatar_real(valor):
            try:
                return locale.currency(valor, grouping=True, symbol=True)
            except Exception:
                return (
                    f"R$ {valor:,.2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

        data_req = request.get_json()
        data_inicio = data_req.get("data_inicio")
        data_fim = data_req.get("data_fim")
        conta_id = data_req.get("conta_id")

        conta = None
        if conta_id:
            conta = Conta.query.get(conta_id)
            if not conta:
                return jsonify({"success": False, "error": "Conta não encontrada"}), 404

        query = MovimentacaoConta.query.filter_by(conta_id=conta_id)

        if data_inicio:
            try:
                data_inicio_dt = datetime.fromisoformat(data_inicio)
                query = query.filter(MovimentacaoConta.data >= data_inicio_dt)
            except ValueError:
                return (
                    jsonify(
                        {"success": False, "error": "Formato de data início inválido"}
                    ),
                    400,
                )

        if data_fim:
            try:
                data_fim_dt = datetime.fromisoformat(data_fim)
                data_fim_dt = data_fim_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(MovimentacaoConta.data <= data_fim_dt)
            except ValueError:
                return (
                    jsonify(
                        {"success": False, "error": "Formato de data fim inválido"}
                    ),
                    400,
                )

        movimentacoes = query.order_by(MovimentacaoConta.data.desc()).all()

        logger.info(
            f"PDF - Conta {conta_id}: {len(movimentacoes)} movimentações encontradas"
        )
        for mov in movimentacoes:
            logger.info(
                f"Mov {mov.id}: {mov.data} | {mov.tipo.value} | {mov.valor} | {mov.descricao}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=20,
            leftMargin=20,
            topMargin=30,
            bottomMargin=30,
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor("#6c5ce7"),
        )

        titulo = f"Relatório de Movimentações - Conta {conta_id}"
        if conta and conta.usuario:
            titulo += f" - {conta.usuario.nome}"
        elements.append(Paragraph(titulo, title_style))

        if conta:
            info_conta = [f"Saldo Atual: {formatar_real(float(conta.saldo_total))}"]
            elements.append(Paragraph(" | ".join(info_conta), styles["Normal"]))

        if data_inicio and data_fim:
            try:
                data_inicio_fmt = datetime.fromisoformat(data_inicio).strftime(
                    "%d/%m/%Y"
                )
                data_fim_fmt = datetime.fromisoformat(data_fim).strftime("%d/%m/%Y")
                periodo_text = f"Período: {data_inicio_fmt} a {data_fim_fmt}"
            except ValueError:
                periodo_text = f"Período: {data_inicio} a {data_fim}"
        else:
            periodo_text = "Período: Todos"

        elements.append(Paragraph(periodo_text, styles["Normal"]))
        elements.append(Spacer(1, 12))

        if movimentacoes:
            table_data = [
                ["Data", "Usuário", "Tipo", "Forma Pagamento", "Valor", "Descrição"]
            ]
            total_entradas = 0
            total_saidas = 0
            total_transferencias = 0

            for mov in movimentacoes:
                valor = float(mov.valor)

                if mov.tipo.value == "entrada":
                    total_entradas += valor
                    tipo_exibicao = "ENTRADA"
                elif mov.tipo.value == "saida":
                    total_saidas += valor
                    tipo_exibicao = "SAÍDA"
                elif mov.tipo.value == "transferencia":
                    total_transferencias += valor
                    tipo_exibicao = "TRANSFERÊNCIA"
                elif mov.tipo.value == "saida_estorno":
                    total_saidas += valor
                    tipo_exibicao = "ESTORNO SAÍDA"
                else:
                    tipo_exibicao = mov.tipo.value.upper()

                table_data.append(
                    [
                        mov.data.strftime("%d/%m/%Y %H:%M") if mov.data else "-",
                        mov.usuario.nome if mov.usuario else "-",
                        tipo_exibicao,
                        mov.forma_pagamento.value.replace("_", " ").title(),
                        formatar_real(valor),
                        Paragraph(mov.descricao or "-", styles["Normal"]),
                    ]
                )

            col_widths = [
                1.2 * inch,
                1.5 * inch,
                1.0 * inch,
                1.3 * inch,
                1.0 * inch,
                2.0 * inch,
            ]

            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c5ce7")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-2, -1), "CENTER"),
                        ("ALIGN", (4, 1), (4, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                    ]
                )
            )
            elements.append(table)

            elements.append(Spacer(1, 12))
            saldo_total = total_entradas - total_saidas - total_transferencias

            totais_data = [
                [
                    f"Entradas: {formatar_real(total_entradas)}",
                    f"Saídas: {formatar_real(total_saidas)}",
                    f"Transferências: {formatar_real(total_transferencias)}",
                ]
            ]

            totais_table = Table(
                totais_data, colWidths=[1.8 * inch, 1.8 * inch, 2.0 * inch]
            )
            totais_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ]
                )
            )
            elements.append(totais_table)

            elements.append(Spacer(1, 8))
            resumo_text = f"Total de movimentações: {len(movimentacoes)} | Saldo final: {formatar_real(saldo_total)}"
            elements.append(Paragraph(resumo_text, styles["Normal"]))

            elements.append(Spacer(1, 4))
            estatisticas_text = (
                f"Entradas: {sum(1 for m in movimentacoes if m.tipo.value == 'entrada')} | "
                f"Saídas: {sum(1 for m in movimentacoes if m.tipo.value == 'saida')} | "
                f"Transferências: {sum(1 for m in movimentacoes if m.tipo.value == 'transferencia')}"
            )
            elements.append(Paragraph(estatisticas_text, styles["Normal"]))

        else:
            elements.append(
                Paragraph(
                    "Nenhuma movimentação encontrada para esta conta no período selecionado.",
                    styles["Normal"],
                )
            )

        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'relatorio_movimentacoes_conta_{conta_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype="application/pdf",
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/produtos/ativos", methods=["GET"])
@login_required
@admin_required
def obter_produtos_ativos():
    """Retorna todos os produtos ativos para filtros"""
    try:
        produtos = Produto.query.filter_by(ativo=True).all()
        resultado = []
        for produto in produtos:
            resultado.append(
                {
                    "id": produto.id,
                    "nome": produto.nome,
                    "marca": produto.marca,
                    "codigo": produto.codigo,
                    "unidade": produto.unidade.value if produto.unidade else None,
                    "estoque_loja": (
                        format_number(produto.estoque_loja, is_weight=True)
                        if produto.estoque_loja
                        else "0,000"
                    ),
                    "estoque_deposito": (
                        format_number(produto.estoque_deposito, is_weight=True)
                        if produto.estoque_deposito
                        else "0,000"
                    ),
                    "estoque_fabrica": (
                        format_number(produto.estoque_fabrica, is_weight=True)
                        if produto.estoque_fabrica
                        else "0,000"
                    ),
                    "valor_unitario": (
                        format_currency(produto.valor_unitario)
                        if produto.valor_unitario
                        else "R$ 0,00"
                    ),
                }
            )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/lotes", methods=["GET"])
@login_required
@admin_required
def obter_todos_lotes():
    """Retorna todos os lotes com informações do produto - COM PAGINAÇÃO"""
    try:
        # Parâmetros de filtro e paginação
        produto_id = request.args.get("produto_id")
        status = request.args.get("status")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 10, type=int)

        # Query base com join no produto
        query = LoteEstoque.query.join(Produto).options(joinedload(LoteEstoque.produto))

        # Aplicar filtros
        if produto_id:
            query = query.filter(LoteEstoque.produto_id == produto_id)

        if status:
            if status == "ativo":
                query = query.filter(
                    LoteEstoque.quantidade_disponivel == LoteEstoque.quantidade_inicial
                )
            elif status == "parcial":
                query = query.filter(
                    LoteEstoque.quantidade_disponivel > 0,
                    LoteEstoque.quantidade_disponivel < LoteEstoque.quantidade_inicial,
                )
            elif status == "esgotado":
                query = query.filter(LoteEstoque.quantidade_disponivel == 0)

        if data_inicio:
            query = query.filter(LoteEstoque.data_entrada >= data_inicio)

        if data_fim:
            query = query.filter(LoteEstoque.data_entrada <= data_fim)

        # Executar query com paginação
        lotes_paginados = query.order_by(LoteEstoque.data_entrada.desc()).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )

        resultado = []
        for lote in lotes_paginados.items:
            # Calcular status do lote
            quantidade_disponivel = float(lote.quantidade_disponivel)
            quantidade_inicial = float(lote.quantidade_inicial)

            if quantidade_disponivel == 0:
                status_lote = "esgotado"
            elif quantidade_disponivel < quantidade_inicial:
                status_lote = "parcial"
            else:
                status_lote = "ativo"

            resultado.append(
                {
                    "id": lote.id,
                    "produto_id": lote.produto_id,
                    "produto_nome": lote.produto.nome if lote.produto else "N/A",
                    "produto_marca": lote.produto.marca if lote.produto else None,
                    "produto_codigo": lote.produto.codigo if lote.produto else None,
                    "quantidade_inicial": format_number(
                        lote.quantidade_inicial, is_weight=True
                    ),
                    "quantidade_disponivel": format_number(
                        lote.quantidade_disponivel, is_weight=True
                    ),
                    "valor_unitario_compra": format_currency(
                        lote.valor_unitario_compra
                    ),
                    "data_entrada": (
                        lote.data_entrada.isoformat() if lote.data_entrada else None
                    ),
                    "observacao": lote.observacao,
                    "status": status_lote,
                }
            )

        return jsonify(
            {
                "lotes": resultado,
                "paginacao": {
                    "pagina_atual": lotes_paginados.page,
                    "total_paginas": lotes_paginados.pages,
                    "total_lotes": lotes_paginados.total,
                    "por_pagina": por_pagina,
                    "tem_anterior": lotes_paginados.has_prev,
                    "tem_proxima": lotes_paginados.has_next,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar lotes: {str(e)}"}), 500


@admin_bp.route("/api/produtos/<int:produto_id>/lotes", methods=["GET"])
@login_required
@admin_required
def obter_lotes_produto(produto_id):
    """Retorna todos os lotes de um produto específico - COM PAGINAÇÃO"""
    try:
        # Parâmetros de paginação
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 10, type=int)

        query = LoteEstoque.query.filter_by(produto_id=produto_id).order_by(
            LoteEstoque.data_entrada.desc()
        )

        # Executar query com paginação
        lotes_paginados = query.paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )

        resultado = []
        for lote in lotes_paginados.items:
            resultado.append(
                {
                    "id": lote.id,
                    "produto_id": lote.produto_id,
                    "quantidade_inicial": format_number(
                        lote.quantidade_inicial, is_weight=True
                    ),
                    "quantidade_disponivel": format_number(
                        lote.quantidade_disponivel, is_weight=True
                    ),
                    "valor_unitario_compra": format_currency(
                        lote.valor_unitario_compra
                    ),
                    "data_entrada": (
                        lote.data_entrada.isoformat() if lote.data_entrada else None
                    ),
                    "observacao": lote.observacao,
                }
            )

        return jsonify(
            {
                "lotes": resultado,
                "paginacao": {
                    "pagina_atual": lotes_paginados.page,
                    "total_paginas": lotes_paginados.pages,
                    "total_lotes": lotes_paginados.total,
                    "por_pagina": por_pagina,
                    "tem_anterior": lotes_paginados.has_prev,
                    "tem_proxima": lotes_paginados.has_next,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar lotes do produto: {str(e)}"}), 500


@admin_bp.route("/api/lotes/<int:lote_id>", methods=["GET"])
@login_required
@admin_required
def obter_lote(lote_id):
    """Retorna um lote específico"""
    try:
        lote = LoteEstoque.query.get_or_404(lote_id)

        return jsonify(
            {
                "id": lote.id,
                "produto_id": lote.produto_id,
                "produto_nome": lote.produto.nome if lote.produto else "N/A",
                "produto_marca": lote.produto.marca if lote.produto else None,
                "quantidade_inicial": format_number(
                    lote.quantidade_inicial, is_weight=True
                ),
                "quantidade_disponivel": format_number(
                    lote.quantidade_disponivel, is_weight=True
                ),
                "valor_unitario_compra": format_currency(lote.valor_unitario_compra),
                "data_entrada": (
                    lote.data_entrada.isoformat() if lote.data_entrada else None
                ),
                "observacao": lote.observacao,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar lote: {str(e)}"}), 500


@admin_bp.route("/api/lotes", methods=["POST"])
@login_required
@admin_required
def criar_lote():
    """Cria um novo lote de estoque - SEM VALIDAÇÕES"""
    try:
        data = request.get_json()

        # Verificar apenas se o produto existe
        if not data.get("produto_id"):
            return jsonify({"error": "ID do produto é obrigatório"}), 400

        produto = Produto.query.get(data["produto_id"])
        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        # Criar novo lote com valores padrão para campos não fornecidos
        novo_lote = LoteEstoque(
            produto_id=data["produto_id"],
            quantidade_inicial=(
                float(data.get("quantidade_inicial", 0).replace(",", "."))
                if data.get("quantidade_inicial")
                else 0
            ),
            quantidade_disponivel=(
                float(
                    data.get(
                        "quantidade_disponivel", data.get("quantidade_inicial", 0)
                    ).replace(",", ".")
                )
                if data.get("quantidade_disponivel") or data.get("quantidade_inicial")
                else 0
            ),
            valor_unitario_compra=(
                float(data.get("valor_unitario_compra", 0).replace(",", "."))
                if data.get("valor_unitario_compra")
                else 0
            ),
            data_entrada=(
                datetime.fromisoformat(data["data_entrada"].replace("Z", "+00:00"))
                if data.get("data_entrada")
                else datetime.now()
            ),
            observacao=data.get("observacao", ""),
        )

        db.session.add(novo_lote)
        db.session.commit()

        # Atualizar estoque do produto
        atualizar_estoque_produto(db, produto.id)

        return (
            jsonify({"message": "Lote criado com sucesso", "lote_id": novo_lote.id}),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao criar lote: {str(e)}"}), 500


@admin_bp.route("/api/lotes/<int:lote_id>", methods=["PUT"])
@login_required
@admin_required
def atualizar_lote(lote_id):
    """Atualiza um lote existente"""
    try:
        lote = LoteEstoque.query.get_or_404(lote_id)
        data = request.get_json()

        # Flag para verificar se houve alterações no lote
        alteracoes_lote = False
        # Flag para verificar se precisa atualizar estoque do produto
        precisa_atualizar_estoque = False

        # Função auxiliar para converter valores
        def converter_valor(valor):
            if valor is None:
                return None
            if isinstance(valor, (int, float)):
                return float(valor)
            if isinstance(valor, str):
                # Remove possíveis formatações e converte
                valor_limpo = (
                    valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
                )
                return float(valor_limpo) if valor_limpo else 0.0
            return float(valor)

        # Atualizar APENAS os campos que foram fornecidos
        if "quantidade_inicial" in data and data["quantidade_inicial"] is not None:
            quantidade_inicial = converter_valor(data["quantidade_inicial"])
            if abs(float(lote.quantidade_inicial) - quantidade_inicial) > 0.001:
                lote.quantidade_inicial = quantidade_inicial
                alteracoes_lote = True

        if (
            "quantidade_disponivel" in data
            and data["quantidade_disponivel"] is not None
        ):
            quantidade_disponivel = converter_valor(data["quantidade_disponivel"])
            if abs(float(lote.quantidade_disponivel) - quantidade_disponivel) > 0.001:
                lote.quantidade_disponivel = quantidade_disponivel
                alteracoes_lote = True
                precisa_atualizar_estoque = True

        if (
            "valor_unitario_compra" in data
            and data["valor_unitario_compra"] is not None
        ):
            valor_unitario = converter_valor(data["valor_unitario_compra"])
            if abs(float(lote.valor_unitario_compra or 0) - valor_unitario) > 0.001:
                lote.valor_unitario_compra = valor_unitario
                alteracoes_lote = True

        if "data_entrada" in data and data["data_entrada"]:
            try:
                nova_data = datetime.fromisoformat(
                    data["data_entrada"].replace("Z", "+00:00")
                )
                if lote.data_entrada != nova_data:
                    lote.data_entrada = nova_data
                    alteracoes_lote = True
            except ValueError as e:
                return jsonify({"error": f"Formato de data inválido: {str(e)}"}), 400

        if "observacao" in data:
            nova_observacao = data["observacao"] or ""
            if lote.observacao != nova_observacao:
                lote.observacao = nova_observacao
                alteracoes_lote = True

        # Apenas commitar se houve alterações no lote
        if alteracoes_lote:
            lote.atualizado_em = datetime.now()
            db.session.commit()

            # Atualizar estoque do produto APENAS se a quantidade disponível mudou
            if precisa_atualizar_estoque:
                atualizar_estoque_produto(db, lote.produto_id, lote_id)

            return jsonify(
                {
                    "sucess": True,
                    "message": "Lote atualizado com sucesso",
                    "alteracoes": alteracoes_lote,
                    "estoque_atualizado": precisa_atualizar_estoque,
                }
            )
        else:
            return jsonify(
                {
                    "sucess": False,
                    "message": "Nenhuma alteração detectada",
                    "alteracoes": False,
                }
            )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao atualizar lote: {str(e)}"}), 500


@admin_bp.route("/api/produtos/<int:produto_id>", methods=["GET"])
@login_required
@admin_required
def obter_produto_id(produto_id):
    """Retorna informações de um produto específico"""
    try:
        produto = Produto.query.get_or_404(produto_id)

        return jsonify(
            {
                "id": produto.id,
                "nome": produto.nome,
                "marca": produto.marca,
                "codigo": produto.codigo,
                "unidade": produto.unidade.value if produto.unidade else None,
                "valor_unitario": (
                    format_currency(produto.valor_unitario)
                    if produto.valor_unitario
                    else "R$ 0,00"
                ),
                "valor_unitario_compra": (
                    format_currency(produto.valor_unitario_compra)
                    if produto.valor_unitario_compra
                    else "R$ 0,00"
                ),
                "estoque_loja": (
                    format_number(produto.estoque_loja, is_weight=True)
                    if produto.estoque_loja
                    else "0,000"
                ),
                "estoque_deposito": (
                    format_number(produto.estoque_deposito, is_weight=True)
                    if produto.estoque_deposito
                    else "0,000"
                ),
                "estoque_fabrica": (
                    format_number(produto.estoque_fabrica, is_weight=True)
                    if produto.estoque_fabrica
                    else "0,000"
                ),
                "estoque_minimo": (
                    format_number(produto.estoque_minimo, is_weight=True)
                    if produto.estoque_minimo
                    else "0,000"
                ),
                "estoque_maximo": (
                    format_number(produto.estoque_maximo, is_weight=True)
                    if produto.estoque_maximo
                    else None
                ),
                "ativo": produto.ativo,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar produto: {str(e)}"}), 500


# Rota para estatísticas de lotes
@admin_bp.route("/api/lotes/estatisticas", methods=["GET"])
@login_required
@admin_required
def obter_estatisticas_lotes():
    """Retorna estatísticas gerais sobre os lotes"""
    try:
        total_lotes = LoteEstoque.query.count()

        # Lotes por status
        lotes_ativos = (
            db.session.query(LoteEstoque)
            .filter(LoteEstoque.quantidade_disponivel == LoteEstoque.quantidade_inicial)
            .count()
        )

        lotes_parciais = (
            db.session.query(LoteEstoque)
            .filter(
                LoteEstoque.quantidade_disponivel > 0,
                LoteEstoque.quantidade_disponivel < LoteEstoque.quantidade_inicial,
            )
            .count()
        )

        lotes_esgotados = (
            db.session.query(LoteEstoque)
            .filter(LoteEstoque.quantidade_disponivel == 0)
            .count()
        )

        # Quantidade total disponível
        quantidade_total = (
            db.session.query(func.sum(LoteEstoque.quantidade_disponivel)).scalar() or 0
        )

        # Valor total em estoque
        valor_total = (
            db.session.query(
                func.sum(
                    LoteEstoque.quantidade_disponivel
                    * LoteEstoque.valor_unitario_compra
                )
            ).scalar()
            or 0
        )

        return jsonify(
            {
                "total_lotes": total_lotes,
                "lotes_ativos": lotes_ativos,
                "lotes_parciais": lotes_parciais,
                "lotes_esgotados": lotes_esgotados,
                "quantidade_total": format_number(quantidade_total, is_weight=True),
                "valor_total": format_currency(valor_total),
            }
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar estatísticas: {str(e)}"}), 500


# ---------------- CONFIGURAÇÕES -----------------
@admin_bp.route("/configuracoes", methods=["GET"])
@login_required
@admin_required
def obter_configuracoes():
    try:
        config = Configuracao.get_config(db.session)
        return (
            jsonify(
                {
                    "success": True,
                    "permitir_venda_sem_estoque": config.permitir_venda_sem_estoque,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Erro ao carregar configurações: {str(e)}",
                }
            ),
            500,
        )


@admin_bp.route("/configuracoes", methods=["POST"])
@login_required
@admin_required
def salvar_configuracoes():
    data = request.get_json() or {}

    permitir_venda_sem_estoque = bool(data.get("permitir_venda_sem_estoque", False))

    try:
        config = Configuracao.get_config(db.session)
        config.permitir_venda_sem_estoque = permitir_venda_sem_estoque
        db.session.commit()

        return (
            jsonify(
                {"success": True, "message": "Configurações atualizadas com sucesso."}
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {"success": False, "message": f"Erro ao salvar configurações: {str(e)}"}
            ),
            500,
        )


@admin_bp.route("/formas-pagamento", methods=["GET"])
@login_required
@admin_required
def formas_pagamento():
    logger.info(f"Acessando formas de pagamento - Usuário: {current_user.nome}")

    forma_pagamento_filtro = request.args.get("forma_pagamento")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    operador_id = request.args.get("operador_id")

    logger.info(
        f"Filtros formas de pagamento - forma_pagamento: {forma_pagamento_filtro}, "
        f"data_inicio: {data_inicio}, data_fim: {data_fim}, operador_id: {operador_id}"
    )

    return render_template(
        "formas_pagamento.html",
        nome_usuario=current_user.nome,
        forma_pagamento_filtro=forma_pagamento_filtro or "",
        data_inicio_filtro=data_inicio or "",
        data_fim_filtro=data_fim or "",
        operador_id_filtro=operador_id or "",
    )


@admin_bp.route("/caixas/financeiro/todos", methods=["GET"])
@login_required
@admin_required
def get_todos_caixas_financeiro():
    try:
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        forma_pagamento = request.args.get("forma_pagamento")
        operador_id = request.args.get("operador_id")
        caixa_id = request.args.get("caixa_id")

        query = db.session.query(Caixa)

        if data_inicio and data_fim:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(
                Caixa.data_abertura.between(data_inicio_dt, data_fim_dt)
            )
        elif data_inicio:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            data_fim_dt = data_inicio_dt + timedelta(days=1)
            query = query.filter(
                Caixa.data_abertura.between(data_inicio_dt, data_fim_dt)
            )
        elif data_fim:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Caixa.data_abertura <= data_fim_dt)

        if operador_id:
            query = query.filter(Caixa.operador_id == operador_id)
        if caixa_id:
            query = query.filter(Caixa.id == caixa_id)

        caixas = query.order_by(Caixa.data_abertura.desc()).all()

        resultado = []
        totais_formas = {}
        estornos_por_forma_global = {}

        for caixa in caixas:
            pagamentos_notas = (
                db.session.query(
                    PagamentoNotaFiscal.forma_pagamento,
                    func.sum(PagamentoNotaFiscal.valor),
                )
                .join(NotaFiscal, PagamentoNotaFiscal.nota_fiscal_id == NotaFiscal.id)
                .filter(
                    NotaFiscal.caixa_id == caixa.id,
                    NotaFiscal.status == StatusNota.emitida,
                )
            )

            if forma_pagamento:
                pagamentos_notas = pagamentos_notas.filter(
                    PagamentoNotaFiscal.forma_pagamento == forma_pagamento
                )

            pagamentos_notas = pagamentos_notas.group_by(
                PagamentoNotaFiscal.forma_pagamento
            ).all()

            pagamentos_contas = db.session.query(
                PagamentoContaReceber.forma_pagamento,
                func.sum(PagamentoContaReceber.valor_pago),
            ).filter(PagamentoContaReceber.caixa_id == caixa.id)

            if forma_pagamento:
                pagamentos_contas = pagamentos_contas.filter(
                    PagamentoContaReceber.forma_pagamento == forma_pagamento
                )

            pagamentos_contas = pagamentos_contas.group_by(
                PagamentoContaReceber.forma_pagamento
            ).all()

            total_caixa_formas = 0

            for forma, total in pagamentos_notas:
                if total:
                    valor = float(total)
                    totais_formas[forma.value] = (
                        totais_formas.get(forma.value, 0) + valor
                    )
                    total_caixa_formas += valor

            for forma, total in pagamentos_contas:
                if total:
                    valor = float(total)
                    totais_formas[forma.value] = (
                        totais_formas.get(forma.value, 0) + valor
                    )
                    total_caixa_formas += valor

            estornos = (
                db.session.query(func.sum(Financeiro.valor))
                .filter(
                    Financeiro.caixa_id == caixa.id,
                    Financeiro.tipo == TipoMovimentacao.saida_estorno,
                )
                .scalar()
                or 0
            )

            estornos_valor = float(estornos)

            if estornos_valor > 0 and total_caixa_formas > 0:
                for forma, total in pagamentos_notas:
                    if total:
                        proporcao = float(total) / total_caixa_formas
                        valor_estorno = estornos_valor * proporcao
                        estornos_por_forma_global[forma.value] = (
                            estornos_por_forma_global.get(forma.value, 0)
                            + valor_estorno
                        )

                for forma, total in pagamentos_contas:
                    if total:
                        proporcao = float(total) / total_caixa_formas
                        valor_estorno = estornos_valor * proporcao
                        estornos_por_forma_global[forma.value] = (
                            estornos_por_forma_global.get(forma.value, 0)
                            + valor_estorno
                        )

            totais = calcular_formas_pagamento(caixa.id, db.session)
            vendas_por_forma = totais["vendas_por_forma_pagamento"]

            if forma_pagamento:
                formas_filtradas = {
                    forma_pagamento: vendas_por_forma.get(forma_pagamento, 0)
                }
            else:
                formas_filtradas = vendas_por_forma.copy()

            contas_prazo_recebidas = {}
            for forma, valor in totais.get("a_prazo_recebido", []):
                if forma and valor:
                    forma_str = forma.value
                    if not forma_pagamento or forma_str == forma_pagamento:
                        contas_prazo_recebidas[forma_str] = contas_prazo_recebidas.get(
                            forma_str, 0
                        ) + float(valor)

            caixa_info = {
                "id": caixa.id,
                "data_abertura": caixa.data_abertura.isoformat(),
                "data_fechamento": (
                    caixa.data_fechamento.isoformat() if caixa.data_fechamento else None
                ),
                "operador_nome": caixa.operador.nome if caixa.operador else "N/A",
                "status": caixa.status.value,
                "totais_gerais": {
                    "entradas": totais["entradas"],
                    "saidas": totais["saidas"],
                    "saldo": totais["saldo"],
                },
                "formas_pagamento": formas_filtradas,
                "contas_prazo_recebidas": contas_prazo_recebidas,
            }

            if forma_pagamento:
                if (
                    formas_filtradas.get(forma_pagamento, 0) > 0
                    or contas_prazo_recebidas.get(forma_pagamento, 0) > 0
                ):
                    resultado.append(caixa_info)
            else:
                resultado.append(caixa_info)

        for forma, estorno in estornos_por_forma_global.items():
            if forma in totais_formas:
                totais_formas[forma] -= estorno

        for forma in list(totais_formas.keys()):
            if totais_formas[forma] < 0:
                totais_formas[forma] = 0

        total_geral = sum(totais_formas.values())

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        caixas_paginados = resultado[start_idx:end_idx]

        return jsonify(
            {
                "success": True,
                "caixas": caixas_paginados,
                "paginacao": {
                    "pagina_atual": page,
                    "por_pagina": per_page,
                    "total": len(resultado),
                    "total_paginas": (len(resultado) + per_page - 1) // per_page,
                },
                "filtros": {
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "forma_pagamento": forma_pagamento,
                    "operador_id": operador_id,
                    "caixa_id": caixa_id,
                },
                "totais_por_forma_pagamento": {
                    f: format_currency(v) for f, v in totais_formas.items()
                },
                "total_geral_formas_pagamento": format_currency(total_geral),
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.session.close()


@admin_bp.route("/caixas/operadores/formas-pagamento", methods=["GET"])
@login_required
@admin_required
def get_operadores_formas_pagamento():
    try:
        operadores = db.session.query(Usuario).filter(Usuario.tipo == "operador").all()
        return jsonify(
            {
                "success": True,
                "operadores": [{"id": op.id, "nome": op.nome} for op in operadores],
            }
        )
    except Exception as e:
        logger.error(f"Erro ao buscar operadores: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.session.close()


@admin_bp.route("/api/caixas/nao-aprovados", methods=["GET"])
@login_required
@admin_required
def get_caixas_financeiro_todos():
    operador_id = request.args.get("operador_id", type=int)
    if not operador_id:
        return jsonify({"success": False, "message": "Operador ID é obrigatório"}), 400

    try:
        caixas = get_caixas_fechado(db.session, operador_id)
        if not caixas:
            return jsonify({"success": True, "data": []})

        data = []
        for c in caixas:
            valores_caixa = calcular_formas_pagamento(c.id, db.session)

            # mantém como Decimal
            total_vendas = sum(
                Decimal(str(v))
                for v in valores_caixa.get("vendas_por_forma_pagamento", {}).values()
            )

            a_prazo_recebido = valores_caixa.get("a_prazo_recebido", [])
            total_a_prazo = sum(Decimal(str(valor)) for _, valor in a_prazo_recebido)

            valor_total = total_vendas + total_a_prazo

            data.append(
                {
                    "id": c.id,
                    "operador_id": c.operador_id,
                    "data_abertura": c.data_abertura.strftime("%Y-%m-%d %H:%M:%S"),
                    "valor_abertura": float(c.valor_abertura),
                    "valor_fechamento": (
                        float(c.valor_fechamento) if c.valor_fechamento else None
                    ),
                    "valor_total_calculado": float(valor_total),
                    "status": c.status.value,
                    "observacoes_operador": c.observacoes_operador,
                    "vendas_por_forma_pagamento": {
                        k: float(v)
                        for k, v in valores_caixa.get(
                            "vendas_por_forma_pagamento", {}
                        ).items()
                    },
                    "a_prazo_recebido": [
                        {"forma_pagamento": forma.value, "valor": float(valor)}
                        for forma, valor in a_prazo_recebido
                    ],
                }
            )

        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Erro ao buscar caixas do operador {operador_id}: {e}")
        return (
            jsonify({"success": False, "message": "Erro interno ao buscar caixas"}),
            500,
        )
    finally:
        db.session.close()


# -------- ROTAS DE VENDAS (ADMIN) --------
@admin_bp.route("/vendas/<int:nota_id>", methods=["GET"])
@login_required
@admin_required
def admin_get_venda_completa(nota_id):
    """Rota para buscar todos os dados completos de uma venda."""
    try:
        dados = get_venda_completa(db.session, nota_id)
        if not dados:
            return jsonify({"success": False, "message": "Venda não encontrada"}), 404
        return jsonify({"success": True, "data": dados}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao buscar venda {nota_id}: {e}")
        return jsonify({"success": False, "message": "Erro ao buscar venda"}), 500
    finally:
        db.session.close()


@admin_bp.route("/vendas/<int:nota_id>", methods=["PUT"])
@login_required
@admin_required
def admin_atualizar_venda(nota_id):
    """Rota para atualizar uma venda existente, aplicando apenas alterações reais."""
    try:
        novos_dados = request.get_json()
        if not novos_dados:
            return (
                jsonify({"success": False, "message": "Dados inválidos ou ausentes"}),
                400,
            )

        dados_atualizados = atualizar_venda(db.session, nota_id, novos_dados)
        return jsonify({"success": True, "data": dados_atualizados}), 200
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"success": False, "message": str(ve)}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar venda {nota_id}: {e}")
        return jsonify({"success": False, "message": "Erro ao atualizar venda"}), 500
    finally:
        db.session.close()


@admin_bp.route("/api/lotes", methods=["GET"])
@login_required
@admin_required
def listar_lotes():
    query = LoteEstoque.query.join(Produto)

    produto_id = request.args.get("produto_id", type=int)
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    pagina = request.args.get("pagina", default=1, type=int)
    por_pagina = 10

    if produto_id:
        query = query.filter(LoteEstoque.produto_id == produto_id)

    if data_inicio:
        try:
            # Início do dia: 2025-11-27 00:00:00
            dt_inicio = datetime.strptime(
                f"{data_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(LoteEstoque.data_entrada >= dt_inicio)
            print(f"Filtro início: >= {dt_inicio}")
        except ValueError:
            pass

    if data_fim:
        try:
            # Fim do dia: 2025-11-27 23:59:59
            dt_fim = datetime.strptime(f"{data_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")
            query = query.filter(LoteEstoque.data_entrada <= dt_fim)
            print(f"Filtro fim: <= {dt_fim}")
        except ValueError:
            pass

    total_lotes = query.count()
    print(f"Total encontrado: {total_lotes}")

    total_paginas = max(1, ceil(total_lotes / por_pagina))

    lotes_pag = (
        query.order_by(LoteEstoque.data_entrada.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    resultado = []
    for lote in lotes_pag:
        resultado.append(
            {
                "id": lote.id,
                "produto_id": lote.produto_id,
                "produto_nome": lote.produto.nome if lote.produto else None,
                "quantidade_inicial": str(lote.quantidade_inicial),
                "quantidade_disponivel": str(lote.quantidade_disponivel),
                "valor_unitario_compra": str(lote.valor_unitario_compra),
                "data_entrada": lote.data_entrada.isoformat(),
                "status": "ativo" if lote.ativo else "inativo",
                "observacao": lote.observacao,
            }
        )

    paginacao = {
        "pagina_atual": pagina,
        "por_pagina": por_pagina,
        "total_lotes": total_lotes,
        "total_paginas": total_paginas,
        "tem_anterior": pagina > 1,
        "tem_proxima": pagina < total_paginas,
    }

    return jsonify({"lotes": resultado, "paginacao": paginacao})


@admin_bp.route("/dashboard/entrada-lotes")
@login_required
@admin_required
def entrada_lotes():
    logger.info(f"Acessando dashboard admin - Usuário: {current_user.nome}")
    return render_template("lotes.html")
