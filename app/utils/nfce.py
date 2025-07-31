from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
from textwrap import wrap

def formatar_endereco_entrega(endereco) -> str:
    """
    Formata o endereço de entrega no formato padrão:
    Linha 1: Logradouro, número - complemento (se houver)
    Linha 2: Bairro: nome_do_bairro (se diferente do complemento)
    Linha 3: Cidade/Estado - CEP: xxxxx-xxx
    Linha 4: Instruções: texto (se houver)
    """
    if not endereco:
        return ""
    
    # Se for string, tenta converter para dicionário
    if isinstance(endereco, str):
        endereco = endereco.replace("Endereco de entrega:", "").strip()
        parts = [p.strip() for p in endereco.split('-') if p.strip()]
        
        if len(parts) >= 3:
            # Parse da string para estrutura de dados
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
            
            # Converte para dicionário para processamento uniforme
            endereco = {
                "logradouro": logradouro,
                "numero": numero,
                "complemento": complemento if complemento else None,
                "bairro": bairro,
                "cidade": cidade,
                "estado": estado,
                "cep": cep
            }
        else:
            return endereco
    
    # Processa dicionário
    partes = []
    
    # Linha 1: Logradouro, número - complemento
    if endereco.get("logradouro") and endereco.get("numero"):
        linha1 = f"{endereco['logradouro']}, {endereco['numero']}"
        if endereco.get("complemento") and endereco["complemento"].strip():
            linha1 += f" - {endereco['complemento']}"
        partes.append(linha1)
    elif endereco.get("logradouro"):
        linha1 = endereco["logradouro"]
        if endereco.get("numero"):
            linha1 += f", {endereco['numero']}"
        if endereco.get("complemento") and endereco["complemento"].strip():
            linha1 += f" - {endereco['complemento']}"
        partes.append(linha1)
    
    # Linha 2: Bairro (somente se existir e for diferente do complemento)
    bairro = endereco.get("bairro", "").strip()
    complemento = endereco.get("complemento", "").strip()
    
    if bairro and bairro.lower() != complemento.lower():
        partes.append(f"Bairro: {bairro}")
    
    # Linha 3: Cidade/Estado - CEP
    cidade = endereco.get("cidade", "").strip()
    estado = endereco.get("estado", "").strip()
    cep = endereco.get("cep", "").strip()
    
    if cidade or estado or cep:
        linha3_parts = []
        
        # Cidade/Estado
        if cidade and estado:
            estado_upper = estado.upper() if len(estado) == 2 else estado
            linha3_parts.append(f"{cidade}/{estado_upper}")
        elif cidade:
            linha3_parts.append(cidade)
        elif estado:
            estado_upper = estado.upper() if len(estado) == 2 else estado
            linha3_parts.append(estado_upper)
        
        # CEP formatado
        if cep:
            # Remove caracteres não numéricos
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
    
    # Linha 4: Instruções (se existirem)
    instrucoes = endereco.get("instrucoes", "").strip()
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
    y -= 3 * mm
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, "Contato: (87) 9 8152-1788")
    y -= 3 * mm
    
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

    # Endereço de entrega formatado conforme solicitado
    if endereco_entrega:
        endereco_formatado = formatar_endereco_entrega(endereco_entrega)
        print(f"Endereço formatado: {endereco_formatado}")
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