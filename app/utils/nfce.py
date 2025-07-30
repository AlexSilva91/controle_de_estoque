from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
from textwrap import wrap


def formatar_endereco_entrega(endereco) -> str:
    """Formata o endereço de entrega em um formato legível."""
    if not endereco:
        return ""
    
    # Se for string, retorna diretamente
    if isinstance(endereco, str):
        return endereco
    
    # Se for dicionário, formata adequadamente
    partes = []
    # Linha 1: Logradouro, número e complemento
    linha1 = []
    if endereco.get("logradouro"):
        linha1.append(endereco["logradouro"])
    if endereco.get("numero"):
        linha1.append(f", {endereco['numero']}")
    if endereco.get("complemento"):
        linha1.append(f" - {endereco['complemento']}")
    if linha1:
        partes.append("".join(linha1))
    
    # Linha 2: Bairro
    if endereco.get("bairro"):
        partes.append(f"Bairro: {endereco['bairro']}")
    
    # Linha 3: Cidade, estado e CEP
    linha3 = []
    if endereco.get("cidade"):
        linha3.append(endereco["cidade"])
    if endereco.get("estado"):
        linha3.append(f"/{endereco['estado']}")
    if endereco.get("cep"):
        linha3.append(f" - CEP: {endereco['cep']}")
    if linha3:
        partes.append("".join(linha3))
    
    # Linha 4: Instruções
    if endereco.get("instrucoes"):
        partes.append(f"Instruções: {endereco['instrucoes']}")
    
    return "\n".join(partes)


def gerar_nfce_pdf_bobina_bytesio(
    dados_nota: dict,
    nome_operador: str = "",
    nome_cliente: str = "",
    endereco_entrega = None,
    logo_path: str = None
):
    largura = 80 * mm
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN_small = ParagraphStyle(
        name="NormalSmall",
        parent=styleN,
        fontSize=6,  
    )

    # Garante que descrição exista para todos os itens
    for item in dados_nota["itens"]:
        if "descricao" not in item:
            item["descricao"] = f"Produto {item['produto_id']}"

    data = [["Produto", "Qtd", "Unit", "Total"]]
    for item in dados_nota["itens"]:
        descricao_paragraph = Paragraph(item["descricao"], styleN_small)
        data.append([
            descricao_paragraph,
            str(item["quantidade"]),
            f"{item['valor_unitario']:.2f}",
            f"{item['valor_total']:.2f}"
        ])

    altura_base = 95 * mm
    altura_linha_item = 7.5 * mm
    altura_tabela = len(data) * altura_linha_item
    altura_rodape = 55 * mm
    espacamentos = 20 * mm
    altura_total = altura_base + altura_tabela + altura_rodape + espacamentos

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(largura, altura_total))
    y = altura_total - 10 * mm

    # Cabeçalho
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, y, "CAVALCANTI RAÇÕES")
    y -= 5 * mm

    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, "Av. Fernando Bezerra, 123 - Centro - Ouricuri-PE")
    y -= 10 * mm

    # Operador
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5 * mm, y, f"Operador: {nome_operador}")
    y -= 4 * mm

    # Emissão
    emissao = dados_nota.get("data_emissao") or datetime.now()
    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Emissão: {emissao.strftime('%d/%m/%Y %H:%M')}")
    y -= 8 * mm

    # Tabela de itens
    tabela = Table(data, colWidths=[33 * mm, 10 * mm, 12 * mm, 15 * mm], repeatRows=1)
    estilos = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.7),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('LEADING', (0, 0), (-1, -1), 9),
    ]
    for i in range(1, len(data)):
        cor_fundo = colors.whitesmoke if i % 2 == 1 else colors.white
        estilos.append(('BACKGROUND', (0, i), (-1, i), cor_fundo))

    tabela.setStyle(TableStyle(estilos))
    tabela.wrapOn(c, largura, altura_total)
    tabela.drawOn(c, 5 * mm, y - altura_tabela)
    y -= altura_tabela + 4 * mm

    # Totais
    total = sum([item["valor_total"] for item in dados_nota["itens"]])
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(largura - 5 * mm, y, f"TOTAL R$: {total:.2f}")
    y -= 6 * mm

    valor_recebido = dados_nota.get("valor_recebido")
    if valor_recebido is not None:
        troco = float(valor_recebido) - total
        c.setFont("Helvetica", 7)
        c.drawString(5 * mm, y, f"Recebido: R$ {valor_recebido:.2f}")
        c.drawRightString(largura - 5 * mm, y, f"Troco: R$ {troco:.2f}")
        y -= 6 * mm

    # Forma de pagamento
    forma_pagamento = dados_nota.get('forma_pagamento', '')
    if hasattr(forma_pagamento, 'value'):
        forma_pagamento = forma_pagamento.value

    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Pagamento: {forma_pagamento}")
    y -= 8 * mm

    # Cliente
    if nome_cliente:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5 * mm, y, f"Cliente: {nome_cliente}")
        y -= 6 * mm

    # Endereço de entrega (agora trata string ou dicionário)
    if endereco_entrega:
        endereco_formatado = formatar_endereco_entrega(endereco_entrega)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(5 * mm, y, "Endereço de entrega:")
        y -= 4 * mm
        
        c.setFont("Helvetica", 6.5)
        for linha in endereco_formatado.split('\n'):
            if linha.strip():
                c.drawString(5 * mm, y, linha)
                y -= 4 * mm
    else:
        y -= 4 * mm

    # Observações
    obs = dados_nota.get("observacao", "")
    if obs:
        c.setFont("Helvetica-Oblique", 6)
        for linha in wrap(f"Obs: {obs}", width=65):
            c.drawString(5 * mm, y, linha)
            y -= 4.5 * mm

    y -= 4 * mm

    # Rodapé fixo
    altura_minima_rodape = 55 * mm
    if y > altura_minima_rodape:
        y = altura_minima_rodape

    linha_assinatura_largura = 30 * mm
    linha_assinatura_y = y

    c.line(5 * mm, linha_assinatura_y, 5 * mm + linha_assinatura_largura, linha_assinatura_y)
    c.setFont("Helvetica", 6)
    c.drawString(5 * mm, linha_assinatura_y - 5, "Assinatura do Operador")

    x_cliente = largura - 5 * mm - linha_assinatura_largura
    c.line(x_cliente, linha_assinatura_y, x_cliente + linha_assinatura_largura, linha_assinatura_y)
    c.drawString(x_cliente, linha_assinatura_y - 5, "Assinatura do Cliente")

    y = linha_assinatura_y - 12 * mm

    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura / 2, y, "Documento sem valor fiscal")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer