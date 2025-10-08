import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import requests
from dotenv import load_dotenv

from app.crud import calcular_formas_pagamento
from app.database import SessionLocal
from app.models.entities import MovimentacaoEstoque, Produto, Usuario, Caixa
from app.models.entities import TipoMovimentacao
from app.models.entities import Financeiro

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def verificar_internet(url="https://www.google.com", timeout=3):
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


def enviar_resumo_caixa_fechado(caixa_id):
    try:
        if not verificar_internet():
            print("⚠️ Sem conexão com a internet. O relatório do caixa não será enviado.")
            return

        db = SessionLocal()
        
        # Calcula as formas de pagamento usando a função existente
        resumo_caixa = calcular_formas_pagamento(caixa_id, db)
        
        # Busca informações adicionais do caixa
        caixa = db.query(Caixa).filter_by(id=caixa_id).first()
        if not caixa:
            print(f"❌ Caixa ID {caixa_id} não encontrado")
            return

        # Formata as formas de pagamento
        formas_pagamento_texto = ""
        for forma, valor in resumo_caixa['vendas_por_forma_pagamento'].items():
            if valor > 0:
                forma_formatada = forma.replace('_', ' ').title()
                formas_pagamento_texto += f"• {forma_formatada}: R$ {valor:.2f}\n"

        # Monta a mensagem para o Telegram
        mensagem = (
            f"💰 <b>RELATÓRIO DE FECHAMENTO DE CAIXA</b>\n"
            f"🆔 <b>Caixa ID:</b> {caixa.id}\n"
            f"📅 <b>Data:</b> {caixa.data_abertura.strftime('%d/%m/%Y')}\n"
            f"👤 <b>Operador:</b> {caixa.operador.nome if caixa.operador else 'N/A'}\n\n"
            
            f"💵 <b>VALORES DE ABERTURA/FECHAMENTO</b>\n"
            f"• Abertura: R$ {float(caixa.valor_abertura):.2f}\n"
            f"• Fechamento: R$ {float(caixa.valor_fechamento):.2f}\n\n"
            
            f"💳 <b>FORMAS DE PAGAMENTO</b>\n"
            f"{formas_pagamento_texto}\n"
            
            f"📊 <b>RESUMO FINANCEIRO</b>\n"
            f"• Total Entradas: R$ {resumo_caixa['entradas']:.2f - resumo_caixa['estornos']:.2f}\n"
            f"• Total Saídas: R$ {resumo_caixa['saidas']:.2f}\n"
            f"• Estornos: R$ {resumo_caixa['estornos']:.2f}\n"
            
            f"💸 <b>DETALHAMENTO</b>\n"
            f"• Valor Físico (Dinheiro): R$ {resumo_caixa['valor_fisico']:.2f}\n"
            f"• Valor Digital: R$ {resumo_caixa['valor_digital']:.2f}\n"
            f"• A Prazo: R$ {resumo_caixa['a_prazo']:.2f}\n"
            f"• Contas a Prazo Recebidas: R$ {resumo_caixa['contas_prazo_recebidas']:.2f}\n\n"
            
            f"<i>Enviado automaticamente pelo sistema Cavalcanti Rações\nEstornos já Deduzidos do Total de entradas</i>"
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Relatório do caixa {caixa_id} enviado com sucesso!")
        else:
            print(f"❌ Erro ao enviar relatório do caixa: {response.text}")

    except Exception as e:
        print(f"❌ Erro no envio do relatório do caixa {caixa_id}:", str(e))
    finally:
        db.close()


def enviar_resumo_movimentacao_diaria():
    try:
        if not verificar_internet():
            print("⚠️ Sem conexão com a internet. O relatório não será enviado.")
            return

        hoje = datetime.now().date()
        db = SessionLocal()

        # === Movimentações de Estoque ===
        movimentacoes = (
            db.query(MovimentacaoEstoque)
            .filter(MovimentacaoEstoque.data >= datetime(hoje.year, hoje.month, hoje.day))
            .all()
        )

        entradas, saidas = [], []

        for mov in movimentacoes:
            produto = mov.produto
            usuario = mov.usuario

            nome_produto = produto.nome if produto else "Desconhecido"
            tipo_produto = produto.tipo if produto else ""
            usuario_nome = usuario.nome if usuario else "Desconhecido"

            quantidade = Decimal(mov.quantidade).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            valor_unitario = Decimal(mov.valor_unitario).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            valor_total = (quantidade * valor_unitario).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            item_formatado = {
                "nome_produto": nome_produto,
                "tipo_produto": tipo_produto,
                "quantidade": quantidade,
                "valor_unitario": valor_unitario,
                "valor_total": valor_total,
                "usuario": usuario_nome
            }

            if mov.tipo == TipoMovimentacao.entrada:
                entradas.append(item_formatado)
            elif mov.tipo == TipoMovimentacao.saida:
                saidas.append(item_formatado)

        def formatar_lista(titulo, lista):
            if not lista:
                return f"<b>{titulo}</b>\n<i>Sem movimentações</i>\n\n"

            texto = f"<b>{titulo}</b>\n"
            for mov in lista:
                texto += (
                    f"• <b>{mov['nome_produto']} ({mov['tipo_produto']})</b>\n"
                    f"  ↳ Quantidade: <b>{mov['quantidade']} un</b>\n"
                    f"  ↳ Unitário: R$ {mov['valor_unitario']:.2f}\n"
                    f"  ↳ Total: <b>R$ {mov['valor_total']:.2f}</b>\n"
                    f"  ↳ Responsável: <i>{mov['usuario']}</i>\n\n"
                )
            return texto

        texto_saidas = formatar_lista("📤 Saídas", saidas)
        texto_entradas = formatar_lista("📥 Entradas", entradas)

        # === Movimentações Financeiras ===
        financeiros = (
            db.query(Financeiro)
            .filter(Financeiro.data >= datetime(hoje.year, hoje.month, hoje.day))
            .all()
        )

        resumo_financeiro = {}
        total_financeiro = Decimal("0.00")
        total_entrada_financeiro = Decimal("0.00")
        total_saida_financeiro = Decimal("0.00")

        for fin in financeiros:
            categoria = fin.categoria.value if fin.categoria else "Outro"
            valor = Decimal(fin.valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            resumo_financeiro[categoria] = resumo_financeiro.get(categoria, Decimal("0.00")) + valor
            total_financeiro += valor

            if fin.tipo == TipoMovimentacao.entrada:
                total_entrada_financeiro += valor
            elif fin.tipo == TipoMovimentacao.saida:
                total_saida_financeiro += valor

        texto_financeiro = "<b>💰 Financeiro</b>\n"
        if resumo_financeiro:
            for cat, val in resumo_financeiro.items():
                texto_financeiro += f"• {cat.capitalize()}: <b>R$ {val:.2f}</b>\n"
        else:
            texto_financeiro += "<i>Sem movimentações financeiras</i>\n"
        texto_financeiro += f"\n<b>Total Financeiro: R$ {total_financeiro:.2f}</b>\n\n"

        # === Mensagem final ===
        mensagem = (
            f"<b>📊 MOVIMENTAÇÃO DETALHADA - {hoje.strftime('%d/%m/%Y')}</b>\n\n"
            f"{texto_saidas}"
            f"{texto_entradas}"
            f"{texto_financeiro}"
            f"<b>Resumo do dia (baseado no financeiro):</b>\n"
            f"• Total Saídas: <b>R$ {total_saida_financeiro:.2f}</b>\n"
            f"• Total Entradas: <b>R$ {total_entrada_financeiro:.2f}</b>\n"
            f"• Saldo do Dia [Entradas - Saídas]: <b>R$ {(total_entrada_financeiro - total_saida_financeiro):.2f}</b>\n\n"
            f"<i>Enviado automaticamente pelo sistema Cavalcanti Rações</i>"
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Relatório detalhado enviado com sucesso!")
        else:
            print(f"❌ Erro ao enviar: {response.text}")

    except Exception as e:
        print("❌ Erro no envio do relatório:", str(e))
    finally:
        db.close()