from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from io import BytesIO
from datetime import datetime
import qrcode
import os


def gerar_nfce_pdf_bobina(nome_arquivo: str, dados_nota: dict, logo_path: str = None):
    largura = 80 * mm

    # Preparar dados da tabela
    data = [["Produto", "Qtd", "Unit", "Total"]]
    for item in dados_nota["itens"]:
        data.append([
            item["descricao"][:40],  # limite razoável para bobina
            str(item["quantidade"]),
            f"{item['valor_unitario']:.2f}",
            f"{item['valor_total']:.2f}"
        ])

    # Alturas fixas e variáveis para calcular altura total do PDF
    altura_base = 70 * mm  # Cabeçalho + info inicial + espaçamentos
    altura_linha_item = 8 * mm
    altura_tabela = len(data) * altura_linha_item
    altura_qrcode = 35 * mm
    altura_rodape = 12 * mm
    espacamentos = 15 * mm  # espaçamento geral extra

    altura_total = altura_base + altura_tabela + altura_qrcode + altura_rodape + espacamentos

    c = canvas.Canvas(nome_arquivo, pagesize=(largura, altura_total))
    y = altura_total - 5 * mm

    # # Logo centralizado
    # if logo_path and os.path.exists(logo_path):
    #     try:
    #         logo_largura = 80 * mm
    #         logo_altura = 50 * mm
    #         logo_x = (largura - logo_largura) / 2
    #         c.drawImage(logo_path, logo_x, y - logo_altura, width=logo_largura, height=logo_altura, preserveAspectRatio=True)
    #         y -= (logo_altura + 3 * mm)
    #     except Exception:
    #         y -= 5 * mm
    # else:
    #     y -= 5 * mm

    # Nome da empresa
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, y, "CAVALCANTI RAÇÕES")
    y -= 5 * mm

    # Endereço e CNPJ
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, "Av. Fernando Bezerra, 123 - Centro - Ouricuri-PE")
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "CNPJ: 00.000.000/0001-00  IE: 123456789")
    y -= 7 * mm

    # Dados NFC-e
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5 * mm, y, f"NFC-e Nº {dados_nota['numero']} | Série {dados_nota['serie']}")
    y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Emissão: {dados_nota['data_emissao'].strftime('%d/%m/%Y %H:%M')}")
    y -= 8 * mm

    # Tabela de Itens
    tabela = Table(data, colWidths=[33 * mm, 10 * mm, 12 * mm, 15 * mm], repeatRows=1)

    estilos = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),  # Cabeçalho cinza
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]

    # Fundo alternado para as linhas de itens
    for i in range(1, len(data)):
        cor_fundo = colors.whitesmoke if i % 2 == 1 else colors.lightgrey
        estilos.append(('BACKGROUND', (0, i), (-1, i), cor_fundo))

    tabela.setStyle(TableStyle(estilos))

    tabela.wrapOn(c, largura, altura_total)
    tabela.drawOn(c, 5 * mm, y - altura_tabela)
    y -= altura_tabela + 6 * mm

    # Total e pagamento
    total = sum([item["valor_total"] for item in dados_nota["itens"]])
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(largura - 8 * mm, y, f"TOTAL R$: {total:.2f}")
    y -= 7 * mm

    c.setFont("Helvetica", 7)
    c.drawString(5 * mm, y, f"Pagamento: {dados_nota['forma_pagamento']}")
    y -= 12 * mm

    # QR Code centralizado
    qr = qrcode.make(dados_nota["qrcode_url"])
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)
    qr_size = 30 * mm
    c.drawImage(ImageReader(buffer), (largura - qr_size) / 2, y - qr_size, width=qr_size, height=qr_size)
    y -= qr_size + 5 * mm

    # Rodapé
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura / 2, y, "Consulte em: www.nfce.sefaz.uf.gov.br")
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "Documento sem valor fiscal – Exemplo de impressão")

    c.showPage()
    c.save()


# Exemplo de uso
if __name__ == "__main__":
    from datetime import datetime

    dados_nota = {
        "numero": "2025",
        "serie": "1",
        "data_emissao": datetime.now(),
        "forma_pagamento": "DINHEIRO",
        "qrcode_url": "https://www.nfce.sefaz.uf.gov.br/consulta/20250708ABCDEF",
        "itens": [
            {"descricao": "Ração para cães 10kg", "quantidade": 2, "valor_unitario": 75.90, "valor_total": 151.80},
            {"descricao": "Ração para gatos 5kg", "quantidade": 1, "valor_unitario": 59.90, "valor_total": 59.90},
            # Pode adicionar mais itens, altura vai ajustar
        ]
    }

    gerar_nfce_pdf_bobina("nfce_bobina_corrigido(1).pdf", dados_nota, logo_path="app/static/assets/logo.jpeg")
