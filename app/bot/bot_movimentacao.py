import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import requests
from dotenv import load_dotenv

from app.database import SessionLocal
from app.models import MovimentacaoEstoque, Produto, Usuario
from app.models import TipoMovimentacao  # Importar o Enum

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def verificar_internet(url="https://www.google.com", timeout=3):
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


def enviar_resumo_movimentacao_diaria():
    try:
        if not verificar_internet():
            print("⚠️ Sem conexão com a internet. O relatório não será enviado.")
            return

        hoje = datetime.utcnow().date()
        db = SessionLocal()

        movimentacoes = (
            db.query(MovimentacaoEstoque)
            .filter(MovimentacaoEstoque.data >= datetime(hoje.year, hoje.month, hoje.day))
            .all()
        )

        entradas = []
        saidas = []
        total_entradas = Decimal("0.00")
        total_saidas = Decimal("0.00")

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
                total_entradas += valor_total
            elif mov.tipo == TipoMovimentacao.saida:
                saidas.append(item_formatado)
                total_saidas += valor_total

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

        # INVERTENDO A ORDEM: SAÍDAS PRIMEIRO
        texto_saidas = formatar_lista("📤 Saídas", saidas)
        texto_entradas = formatar_lista("📥 Entradas", entradas)

        mensagem = (
            f"<b>📊 MOVIMENTAÇÃO DETALHADA - {hoje.strftime('%d/%m/%Y')}</b>\n\n"
            f"{texto_saidas}"
            f"{texto_entradas}"
            f"<b>Resumo do dia:</b>\n"
            f"• Total Saídas: <b>R$ {total_saidas:.2f}</b>\n"
            f"• Total Entradas: <b>R$ {total_entradas:.2f}</b>\n"
            f"• Saldo do Dia [Entradas - Saídas]: <b>R$ {(total_saidas - total_entradas):.2f}</b>\n\n"
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
