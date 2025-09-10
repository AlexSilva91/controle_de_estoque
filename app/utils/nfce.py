from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
from textwrap import wrap
import os
from PIL import Image as PILImage  # Para obter as dimensões originais da imagem

def safe_float(value, default=0.0):
    """Converte para float com tratamento seguro para None e valores inválidos"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_str(value, default=""):
    """Converte para string com tratamento seguro para None"""
    return str(value) if value is not None else default

def format_number(value):
    """Formata números com 2 casas decimais, removendo .00 quando inteiro"""
    return f"{value:.2f}".replace(".00", "") if value == int(value) else f"{value:.2f}"

def formatar_endereco_entrega(endereco) -> str:
    """Formata o endereço de entrega com tratamento seguro para valores nulos"""
    if not endereco or not isinstance(endereco, dict):
        return ""
    
    logradouro = safe_str(endereco.get("logradouro"))
    numero = safe_str(endereco.get("numero"))
    complemento = safe_str(endereco.get("complemento"))
    bairro = safe_str(endereco.get("bairro"))
    cidade = safe_str(endereco.get("cidade"))
    estado = safe_str(endereco.get("estado"))
    cep = safe_str(endereco.get("cep"))
    instrucoes = safe_str(endereco.get("instrucoes"))

    partes = []
    
    if logradouro:
        linha = logradouro
        if numero:
            linha += f", {numero}"
        if complemento:
            linha += f" - {complemento}"
        partes.append(linha)
    
    if bairro and (not complemento or bairro.lower() != complemento.lower()):
        partes.append(f"Bairro: {bairro}")
    
    linha3 = []
    if cidade:
        if estado:
            linha3.append(f"{cidade}/{estado.upper() if len(estado) == 2 else estado}")
        else:
            linha3.append(cidade)
    elif estado:
        linha3.append(estado.upper() if len(estado) == 2 else estado)
    
    if cep:
        cep_numeros = ''.join(filter(str.isdigit, cep))
        if len(cep_numeros) == 8:
            cep_formatado = f"{cep_numeros[:5]}-{cep_numeros[5:]}"
            if linha3:
                linha3.append(f" - CEP: {cep_formatado}")
            else:
                linha3.append(f"CEP: {cep_formatado}")
    
    if linha3:
        partes.append("".join(linha3))
    
    if instrucoes:
        partes.append("Instruções:")
        for linha in wrap(instrucoes, width=48):
            partes.append(f"  {linha}")
    
    return "\n".join(partes)

def gerar_nfce_pdf_bobina_bytesio(dados_nota: dict) -> BytesIO:
    largura = 80 * mm
    styles = getSampleStyleSheet()

    # Estilo pequeno (usado em textos extras)
    styleN_small = ParagraphStyle(
        name="NormalSmall",
        parent=styles["Normal"],
        fontSize=5,
        leading=7
    )

    # Estilo negrito e maior para itens da tabela
    styleItemBold = ParagraphStyle(
        name="ItemBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8
    )

    from flask import current_app
    logo_path = os.path.join(current_app.root_path, 'static', 'assets', 'logo.jpeg')

    produtos = dados_nota.get("produtos", []) or []
    operador = dados_nota.get("operador", {}) or {}
    cliente = dados_nota.get("cliente", {}) or {}
    formas_pagamento = dados_nota.get("formas_pagamento", []) or []
    endereco_entrega = dados_nota.get("endereco_entrega", {}) or {}
    metadados = dados_nota.get("metadados", {}) or {}
    codigo_nota = dados_nota.get("nota_fiscal_id") or {}
    
    try:
        emissao_str = dados_nota.get("data_emissao", "")
        emissao = datetime.strptime(emissao_str, "%Y-%m-%dT%H:%M:%S") if emissao_str else datetime.now()
    except ValueError:
        emissao = datetime.now()

    valor_total_nota = safe_float(dados_nota.get("valor_total_nota"))
    valor_total_sem_desconto = safe_float(dados_nota.get("valor_total_sem_desconto"))
    desconto_total = max(valor_total_sem_desconto - valor_total_nota, 0)

    tem_descontos = desconto_total > 0 or any(
        safe_float(p.get("desconto_aplicado")) > 0 
        for p in produtos if p is not None
    )

    if tem_descontos:
        data = [["Produto", "Qtd", "Unit", "Desc", "Total"]]
        col_widths = [30*mm, 8*mm, 10*mm, 8*mm, 9*mm]
    else:
        data = [["Produto", "Qtd", "Unit", "Total"]]
        col_widths = [34*mm, 10*mm, 12*mm, 15*mm]

    # Agora todos os campos dos produtos já vêm com estilo bold e maior
    for produto in produtos:
        if not produto or not isinstance(produto, dict):
            continue

        nome_produto = Paragraph(
            safe_str(produto.get("nome"), f"Produto {produto.get('id', '')}"),
            styleItemBold
        )
        quantidade = Paragraph(
            format_number(safe_float(produto.get("quantidade"))),
            styleItemBold
        )
        valor_unitario = Paragraph(
            format_number(safe_float(produto.get("valor_unitario"))),
            styleItemBold
        )
        valor_total = Paragraph(
            format_number(
                safe_float(
                    produto.get("valor_total_com_desconto",
                        safe_float(produto.get("valor_unitario")) * safe_float(produto.get("quantidade"))
                    )
                )
            ),
            styleItemBold
        )
        desconto = Paragraph(
            f"-{format_number(safe_float(produto.get('desconto_aplicado')))}"
            if safe_float(produto.get("desconto_aplicado")) > 0 else "-",
            styleItemBold
        )

        if tem_descontos:
            data.append([nome_produto, quantidade, valor_unitario, desconto, valor_total])
        else:
            data.append([nome_produto, quantidade, valor_unitario, valor_total])

    altura_base = 95 * mm
    altura_linha_item = 7 * mm
    altura_tabela = len(data) * altura_linha_item
    altura_rodape = 55 * mm
    espacamentos = 25 * mm
    altura_logo = 25 * mm
    altura_total = altura_base + altura_tabela + altura_rodape + espacamentos + altura_logo

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(largura, altura_total))
    y = altura_total

    # Logo
    if os.path.exists(logo_path):
        try:
            with PILImage.open(logo_path) as img:
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
            max_logo_width = largura
            logo_width = min(max_logo_width, img_width)
            logo_height = logo_width / aspect_ratio
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo_x = (largura - logo_width) / 2
            logo_y = y - logo_height
            logo.wrapOn(c, largura, altura_total)
            logo.drawOn(c, logo_x, logo_y)
            y -= logo_height + 5 * mm
            altura_total += logo_height
        except Exception as e:
            print(f"Erro ao carregar a logo: {e}")

    c.setFont("Helvetica", 7)
    c.drawCentredString(largura/2, y, "Contato: (87) 9 8152-1788")
    y -= 4 * mm
    c.drawCentredString(largura/2, y, "Av. Fernando Bezerra, 123 - Centro - Ouricuri-PE")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(5*mm, y, f"Operador: {safe_str(operador.get('nome'))}")
    y -= 5 * mm

    nome_cliente = safe_str(cliente.get("nome"))
    if nome_cliente:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5*mm, y, f"Cliente: {nome_cliente}")
        y -= 5 * mm

    c.setFont("Helvetica", 7)
    c.drawString(5*mm, y, f"Emissão: {emissao.strftime('%d/%m/%Y %H:%M')}   ID Nota: {codigo_nota}")
    y -= 8 * mm

    # Tabela
    tabela = Table(data, colWidths=col_widths, repeatRows=1)
    estilo = [
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (1,0), (-1,0), 'RIGHT'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 3),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('LEADING', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('WORDWRAP', (0,0), (-1,-1), True),
    ]
    for i in range(1, len(data)):
        estilo.append(('BACKGROUND', (0,i), (-1,i), colors.whitesmoke if i%2 else colors.white))
    tabela.setStyle(TableStyle(estilo))
    tabela.wrapOn(c, largura, altura_total)
    tabela.drawOn(c, 5*mm, y - altura_tabela)
    y -= altura_tabela + 5 * mm

    if desconto_total > 0:
        c.setFont("Helvetica", 7)
        c.drawRightString(largura-5*mm, y, f"DESCONTO: -{format_number(desconto_total)}")
        y -= 4 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(largura-5*mm, y, f"TOTAL R$: {format_number(valor_total_nota)}")
    y -= 8 * mm

    if formas_pagamento:
        c.setFont("Helvetica-Bold", 7)
        c.drawString(5*mm, y, "Pagamentos:")
        y -= 5 * mm
        c.setFont("Helvetica", 7)
        for pgto in formas_pagamento:
            if not pgto or not isinstance(pgto, dict):
                continue
            forma = safe_str(pgto.get("forma_pagamento")).replace("_", " ").title()
            valor = safe_float(pgto.get("valor"))
            c.drawString(10*mm, y, f"{forma}: R$ {format_number(valor)}")
            y -= 4 * mm
    else:
        pgto_especifico = dados_nota.get("pagamento_especifico", {})
        if pgto_especifico and isinstance(pgto_especifico, dict):
            forma = safe_str(pgto_especifico.get("forma_pagamento")).replace("_", " ").title()
            c.setFont("Helvetica", 7)
            c.drawString(5*mm, y, f"Pagamento: {forma}")
            y -= 6 * mm

    if metadados.get("possui_entrega", False) and endereco_entrega:
        endereco = formatar_endereco_entrega(endereco_entrega)
        if endereco:
            c.setFont("Helvetica-Bold", 7)
            c.drawString(5*mm, y, "Entrega:")
            y -= 4 * mm
            c.setFont("Helvetica", 6.5)
            for linha in endereco.split('\n'):
                c.drawString(5*mm, y, linha)
                y -= 4 * mm

    y = max(y, 30*mm)
    c.line(5*mm, y, 35*mm, y)
    c.line(largura-35*mm, y, largura-5*mm, y)
    c.setFont("Helvetica", 6)
    c.drawString(5*mm, y-5, "Assinatura do Operador")
    c.drawString(largura-35*mm, y-5, "Assinatura do Cliente")
    y -= 12 * mm
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura/2, y, "Documento sem valor fiscal")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def generate_caixa_financeiro_pdf(data):
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch, mm
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from io import BytesIO
    import textwrap
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    # Título
    title = Paragraph(f"Relatório Financeiro - Caixa #{data['caixa_id']}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Informações do caixa
    info_data = [
        [Paragraph('<b>Operador:</b>', styles['Normal']), data['operador']],
        [Paragraph('<b>Data Abertura:</b>', styles['Normal']), data['data_abertura']],
        [Paragraph('<b>Data Fechamento:</b>', styles['Normal']), data['data_fechamento']],
        [Paragraph('<b>Status:</b>', styles['Normal']), data['status']]
    ]
    
    info_table = Table(info_data, colWidths=[50*mm, 100*mm])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Tabela de movimentações
    mov_headers = [
        Paragraph('<b>Data</b>', styles['Normal']),
        Paragraph('<b>Tipo</b>', styles['Normal']),
        Paragraph('<b>Categoria</b>', styles['Normal']),
        Paragraph('<b>Valor (R$)</b>', styles['Normal']),
        Paragraph('<b>Descrição</b>', styles['Normal']),
        Paragraph('<b>Cliente</b>', styles['Normal']),
        Paragraph('<b>Formas Pagamento</b>', styles['Normal'])
    ]
    
    mov_data = [mov_headers]
    
    for mov in data['movimentacoes']:
        # Formatar formas de pagamento com quebra de linha
        formas_pagamento = []
        for fp in mov['formas_pagamento']:
            formas_pagamento.append(f"{fp['forma']}: R$ {fp['valor']:.2f}")
        formas_pagamento_text = "<br/>".join(formas_pagamento) if formas_pagamento else "N/A"
        
        # Criar parágrafos para permitir quebra de texto
        mov_data.append([
            Paragraph(mov['data'], styles['Normal']),
            Paragraph(mov['tipo'].capitalize(), styles['Normal']),
            Paragraph(mov['categoria'].capitalize() if mov['categoria'] != 'N/A' else 'N/A', styles['Normal']),
            Paragraph(f"{mov['valor']:.2f}", styles['Normal']),
            Paragraph(mov['descricao'], styles['Normal']),
            Paragraph(mov['cliente_nome'] or 'N/A', styles['Normal']),
            Paragraph(formas_pagamento_text, styles['Normal'])
        ])
    
    # Calcular larguras das colunas (proporcionais ao conteúdo)
    col_widths = [25*mm, 20*mm, 25*mm, 20*mm, 40*mm, 30*mm, 40*mm]
    
    # Criar tabela com as movimentações
    mov_table = Table(mov_data, colWidths=col_widths, repeatRows=1)
    
    # Estilo da tabela
    mov_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(mov_table)
    
    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()