from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
from textwrap import wrap
from decimal import Decimal

def formatar_endereco_entrega(endereco) -> str:
    """
    Formata o endereço de entrega no formato padrão, com todas as proteções contra valores None ou vazios.
    """
    if not endereco:
        return ""

    if isinstance(endereco, str):
        endereco = endereco.replace("Endereco de entrega:", "").strip()
        parts = [p.strip() for p in endereco.split('-') if p.strip()]
        
        if len(parts) >= 3:
            logradouro_numero_comp = parts[0]
            bairro = parts[1]
            cidade_estado_cep = parts[2]
            
            logradouro_parts = logradouro_numero_comp.split(',')
            logradouro = logradouro_parts[0].strip() if logradouro_parts else ""
            numero_comp = logradouro_parts[1].strip() if len(logradouro_parts) > 1 else ""
            
            numero = numero_comp.split(' ')[0] if numero_comp else ""
            complemento = ' '.join(numero_comp.split(' ')[1:]) if len(numero_comp.split(' ')) > 1 else ""
            
            cidade_estado = cidade_estado_cep.split('- CEP:')[0].strip()
            cep = cidade_estado_cep.split('- CEP:')[1].strip() if '- CEP:' in cidade_estado_cep else ""
            
            cidade = cidade_estado.split('/')[0].strip() if '/' in cidade_estado else ""
            estado = cidade_estado.split('/')[1].strip() if '/' in cidade_estado else ""
            
            endereco = {
                "logradouro": logradouro or "",
                "numero": numero or "",
                "complemento": complemento or "",
                "bairro": bairro or "",
                "cidade": cidade or "",
                "estado": estado or "",
                "cep": cep or "",
            }
        else:
            return endereco.strip()

    logradouro = str(endereco.get("logradouro") or "").strip()
    numero = str(endereco.get("numero") or "").strip()
    complemento = str(endereco.get("complemento") or "").strip()
    bairro = str(endereco.get("bairro") or "").strip()
    cidade = str(endereco.get("cidade") or "").strip()
    estado = str(endereco.get("estado") or "").strip()
    cep = str(endereco.get("cep") or "").strip()
    instrucoes = str(endereco.get("instrucoes") or "").strip()

    partes = []

    if logradouro:
        linha1 = logradouro
        if numero:
            linha1 += f", {numero}"
        if complemento:
            linha1 += f" - {complemento}"
        partes.append(linha1)

    if bairro and bairro.lower() != complemento.lower():
        partes.append(f"Bairro: {bairro}")

    linha3_parts = []
    if cidade:
        if estado:
            linha3_parts.append(f"{cidade}/{estado.upper() if len(estado) == 2 else estado}")
        else:
            linha3_parts.append(cidade)
    elif estado:
        linha3_parts.append(estado.upper() if len(estado) == 2 else estado)

    if cep:
        cep_numeros = ''.join(filter(str.isdigit, cep))
        if len(cep_numeros) == 8:
            cep_formatado = f"{cep_numeros[:5]}-{cep_numeros[5:]}"
        else:
            cep_formatado = cep
        if linha3_parts:
            linha3_parts.append(f" - CEP: {cep_formatado}")
        else:
            linha3_parts.append(f"CEP: {cep_formatado}")

    if linha3_parts:
        partes.append("".join(linha3_parts))

    if instrucoes:
        instrucoes_linhas = wrap(instrucoes, width=48)
        partes.append("Instruções:")
        partes.extend([f"  {linha}" for linha in instrucoes_linhas])

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

    itens = dados_nota.get("itens", [])
    tem_descontos = any(item.get('desconto_aplicado', 0) > 0 for item in itens)

    if tem_descontos:
        data = [["Produto", "Qtd", "Unit", "Desc", "Total"]]
        for item in itens:
            descricao = item.get("descricao")
            if not descricao:
                produto_id = item.get("produto_id")
                descricao = f"Produto {produto_id}" if produto_id is not None else "Produto"

            descricao_paragraph = Paragraph(descricao, styleN_small)
            quantidade = item.get("quantidade", 0)
            valor_unitario = item.get("valor_unitario_original", item.get("valor_unitario", 0))
            desconto = item.get("desconto_aplicado", 0)
            valor_total = item.get("valor_total", 0)

            data.append([
                descricao_paragraph,
                f"{quantidade:.2f}",
                f"{valor_unitario:.2f}",
                f"-{desconto:.2f}" if desconto > 0 else "-",
                f"{valor_total:.2f}"
            ])
        col_widths = [28 * mm, 10 * mm, 12 * mm, 10 * mm, 10 * mm]
    else:
        data = [["Produto", "Qtd", "Unit", "Total"]]
        for item in itens:
            descricao = item.get("descricao")
            if not descricao:
                produto_id = item.get("produto_id")
                descricao = f"Produto {produto_id}" if produto_id is not None else "Produto"

            descricao_paragraph = Paragraph(descricao, styleN_small)
            quantidade = item.get("quantidade", 0)
            valor_unitario = item.get("valor_unitario", 0)
            valor_total = item.get("valor_total", 0)

            data.append([
                descricao_paragraph,
                f"{quantidade:.2f}",
                f"{valor_unitario:.2f}",
                f"{valor_total:.2f}"
            ])
        col_widths = [33 * mm, 10 * mm, 12 * mm, 15 * mm]

    altura_base = 95 * mm
    altura_linha_item = 7.5 * mm
    altura_tabela = len(data) * altura_linha_item
    altura_rodape = 55 * mm
    espacamentos = 20 * mm
    altura_total = altura_base + altura_tabela + altura_rodape + espacamentos

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(largura, altura_total))
    y = altura_total - 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, y, "CAVALCANTI RAÇÕES")
    y -= 3 * mm
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, "Contato: (87) 9 8152-1788")
    y -= 3 * mm
    c.drawCentredString(largura / 2, y, "Av. Fernando Bezerra, 123 - Centro - Ouricuri-PE")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(5 * mm, y, f"Operador: {nome_operador}")
    y -= 4 * mm

    emissao = dados_nota.get("data_emissao") or datetime.now()
    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Emissão: {emissao.strftime('%d/%m/%Y %H:%M')}")
    y -= 8 * mm

    tabela = Table(data, colWidths=col_widths, repeatRows=1)
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

    total = sum(item.get("valor_total", 0) for item in itens)
    desconto_total = dados_nota.get("valor_desconto_total", 0)

    if desconto_total > 0:
        c.setFont("Helvetica", 7)
        c.drawRightString(largura - 5 * mm, y, f"DESCONTO TOTAL: -{desconto_total:.2f}")
        y -= 4 * mm

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

    forma_pagamento = dados_nota.get("forma_pagamento", "")
    if hasattr(forma_pagamento, 'value'):
        forma_pagamento = forma_pagamento.value
    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Pagamento: {forma_pagamento}")
    y -= 8 * mm

    if nome_cliente:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5 * mm, y, f"Cliente: {nome_cliente}")
        y -= 6 * mm

    if endereco_entrega:
        endereco_formatado = formatar_endereco_entrega(endereco_entrega)
        if endereco_formatado:
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

    obs = dados_nota.get("observacao", "")
    if obs:
        c.setFont("Helvetica-Oblique", 6)
        for linha in wrap(f"Obs: {obs}", width=65):
            c.drawString(5 * mm, y, linha)
            y -= 4.5 * mm

    y -= 4 * mm

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
