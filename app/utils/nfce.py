from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
from textwrap import wrap

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

def gerar_nfce_pdf_bobina_bytesio(dados_nota: dict, logo_path: str = None) -> BytesIO:
    """Gera PDF de nota fiscal no formato bobina com tratamento completo dos dados
    
    Args:
        dados_nota: Dicionário com os dados da nota fiscal no formato retornado por buscar_pagamentos_notas_fiscais
        logo_path: Caminho opcional para um arquivo de logo
        
    Returns:
        BytesIO: Objeto de bytes com o PDF gerado
    """
    # Configurações básicas do PDF
    largura = 80 * mm
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN_small = ParagraphStyle(
        name="NormalSmall",
        parent=styleN,
        fontSize=5,
        leading=7
    )

    # Extração segura dos dados com valores padrão
    produtos = dados_nota.get("produtos", []) or []
    operador = dados_nota.get("operador", {}) or {}
    cliente = dados_nota.get("cliente", {}) or {}  # Agora vem diretamente do dicionário
    formas_pagamento = dados_nota.get("formas_pagamento", []) or []
    endereco_entrega = dados_nota.get("endereco_entrega", {}) or {}
    metadados = dados_nota.get("metadados", {}) or {}

    # Processamento seguro da data
    try:
        emissao_str = dados_nota.get("data_emissao", "")
        emissao = datetime.strptime(emissao_str, "%Y-%m-%dT%H:%M:%S") if emissao_str else datetime.now()
    except ValueError:
        emissao = datetime.now()

    # Cálculos financeiros com tratamento para None
    valor_total_nota = safe_float(dados_nota.get("valor_total_nota"))
    valor_total_sem_desconto = safe_float(dados_nota.get("valor_total_sem_desconto"))
    desconto_total = max(valor_total_sem_desconto - valor_total_nota, 0)

    # Verifica se há descontos
    tem_descontos = desconto_total > 0 or any(
        safe_float(p.get("desconto_aplicado")) > 0 
        for p in produtos 
        if p is not None
    )

    # Prepara tabela de produtos com larguras ajustadas
    if tem_descontos:
        data = [["Produto", "Qtd", "Unit", "Desc", "Total"]]
        col_widths = [30*mm, 8*mm, 10*mm, 8*mm, 9*mm]  # Mais espaço para produto
    else:
        data = [["Produto", "Qtd", "Unit", "Total"]]
        col_widths = [34*mm, 10*mm, 12*mm, 15*mm]

    for produto in produtos:
        if not produto or not isinstance(produto, dict):
            continue
            
        # Nome completo do produto sem truncamento
        nome_produto = safe_str(produto.get("nome"), f"Produto {produto.get('id', '')}")
        quantidade = safe_float(produto.get("quantidade"))
        valor_unitario = safe_float(produto.get("valor_unitario"))
        valor_total = safe_float(produto.get("valor_total_com_desconto", valor_unitario * quantidade))
        desconto = safe_float(produto.get("desconto_aplicado"))

        descricao = Paragraph(nome_produto, styleN_small)
        
        if tem_descontos:
            data.append([
                descricao,
                format_number(quantidade),
                format_number(valor_unitario),
                f"-{format_number(desconto)}" if desconto > 0 else "-",
                format_number(valor_total)
            ])
        else:
            data.append([
                descricao,
                format_number(quantidade),
                format_number(valor_unitario),
                format_number(valor_total)
            ])

    # Cálculo da altura dinâmica
    altura_base = 95 * mm
    altura_linha_item = 7 * mm
    altura_tabela = len(data) * altura_linha_item
    altura_rodape = 55 * mm
    espacamentos = 25 * mm
    altura_total = altura_base + altura_tabela + altura_rodape + espacamentos

    # Criação do PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(largura, altura_total))
    y = altura_total - 10 * mm

    # Cabeçalho
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura/2, y, "CAVALCANTI RAÇÕES")
    y -= 5 * mm
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura/2, y, "Contato: (87) 9 8152-1788")
    y -= 4 * mm
    c.drawCentredString(largura/2, y, "Av. Fernando Bezerra, 123 - Centro - Ouricuri-PE")
    y -= 10 * mm

    # Informações da nota
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5*mm, y, f"Operador: {safe_str(operador.get('nome'))}")
    y -= 5 * mm
    
    # Nome do cliente - agora vem diretamente do dicionário
    nome_cliente = safe_str(cliente.get("nome"))
    if nome_cliente:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5*mm, y, f"Cliente: {nome_cliente}")
        y -= 5 * mm

    c.setFont("Helvetica", 7)
    c.drawString(5*mm, y, f"Emissão: {emissao.strftime('%d/%m/%Y %H:%M')}")
    y -= 8 * mm

    # Tabela de produtos com estilo melhorado
    tabela = Table(data, colWidths=col_widths, repeatRows=1)
    estilo = [
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (1,0), (-1,0), 'RIGHT'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6),
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

    # Totais
    if desconto_total > 0:
        c.setFont("Helvetica", 7)
        c.drawRightString(largura-5*mm, y, f"DESCONTO: -{format_number(desconto_total)}")
        y -= 4 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(largura-5*mm, y, f"TOTAL R$: {format_number(valor_total_nota)}")
    y -= 8 * mm

    # Formas de pagamento
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

    # Endereço de entrega
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

    # Rodapé
    y = max(y, 30*mm)
    
    # Linhas de assinatura
    c.line(5*mm, y, 35*mm, y)
    c.line(largura-35*mm, y, largura-5*mm, y)
    
    c.setFont("Helvetica", 6)
    c.drawString(5*mm, y-5, "Assinatura do Operador")
    c.drawString(largura-35*mm, y-5, "Assinatura do Cliente")
    
    y -= 12 * mm
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura/2, y, "Documento sem valor fiscal")

    # Finalização
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer