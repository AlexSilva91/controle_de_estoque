"""
tests/integrations/fiscal/test_fiscal_manual_com_calculo_impostos.py

Versão INTEGRADA com cálculo automático de impostos - CORRIGIDA para erro de IE
COM GERAÇÃO DE DOCUMENTOS FORMATADOS
"""

from app.integrations.fiscal_api.service import fiscal_service
import json
from datetime import datetime
from decimal import Decimal
from app import create_app, db
import base64
import os
import xml.dom.minidom

from app.models.fiscal_models import (
    ConfiguracaoFiscal,
    ClienteFiscal,
    ProdutoFiscal,
    Transportadora,
    VeiculoTransporte
)
from app.models.entities import Produto

# Import do calculador de impostos
from app.utils.fiscal.calculo_impostos import CalculadoraImpostos


def determinar_indicador_ie(cliente_fiscal):
    """
    Determina o indicador de IE corretamente com base nos dados do cliente
    
    Valores:
    1 = Contribuinte ICMS (informar a IE do destinatário)
    2 = Contribuinte isento de inscrição
    9 = Não Contribuinte
    """
    # Se tem inscrição estadual válida
    if cliente_fiscal.inscricao_estadual and cliente_fiscal.inscricao_estadual.strip():
        return 1  # Contribuinte ICMS
    
    # Verificar se é isento (não tem IE mas é obrigado)
    # Para simplificar, vamos considerar como não contribuinte (9)
    # Em um sistema real, você teria um campo específico para indicar isenção
    return 9


def calcular_impostos_produto(
    session,
    produto_fiscal_id: int,
    quantidade: float,
    config_fiscal_id: int = 1
) -> dict:
    """
    Calcula impostos automaticamente usando dados do banco
    
    Returns:
        dict com estrutura de impostos para a NF-e
    """
    calc = CalculadoraImpostos()
    
    # Busca configuração fiscal (emitente)
    config = session.query(ConfiguracaoFiscal).filter_by(id=config_fiscal_id).first()
    if not config:
        raise ValueError(f"Configuração fiscal {config_fiscal_id} não encontrada")
    
    # Busca produto fiscal
    produto_fiscal = session.query(ProdutoFiscal).filter_by(id=produto_fiscal_id).first()
    if not produto_fiscal:
        raise ValueError(f"Produto fiscal {produto_fiscal_id} não encontrado")
    
    # Busca produto relacionado (CORRIGIDO - relacionamento muitos-para-muitos)
    session.refresh(produto_fiscal)  # Garante que os produtos estão carregados
    if not produto_fiscal.produtos:
        raise ValueError(f"ProdutoFiscal {produto_fiscal_id} não está relacionado a nenhum produto")
    
    produto = produto_fiscal.produtos[0]
    
    # Determina regime tributário
    regime_map = {
        "1": "SIMPLES_NACIONAL",
        "2": "NORMAL",
        "3": "SIMPLES_NACIONAL"  # MEI tratado como Simples
    }
    regime = regime_map.get(str(config.regime_tributario), "SIMPLES_NACIONAL")
    
    # Valor do produto
    valor_unitario = float(produto.valor_unitario)
    valor_total = Decimal(str(valor_unitario)) * Decimal(str(quantidade))
    
    print(f"\n💰 CALCULANDO IMPOSTOS:")
    print(f"   Regime: {regime}")
    print(f"   Valor Unitário: R$ {valor_unitario:.2f}")
    print(f"   Quantidade: {quantidade}")
    print(f"   Valor Total: R$ {float(valor_total):.2f}")
    
    # ==========================================
    # ICMS
    # ==========================================
    icms_resultado = {}
    
    if regime == "SIMPLES_NACIONAL":
        # Usa CSOSN do produto
        csosn = produto_fiscal.csosn or "102"
        
        # Calcula ICMS Simples Nacional
        icms_calc = calc.calcular_icms_simples_nacional(
            valor_produto=valor_total,
            cst=csosn,
            aliquota_credito=produto_fiscal.aliquota_icms
        )
        
        icms_resultado["CodSituacaoTributaria"] = csosn
        
        # Se tiver crédito (CSOSN 101 ou 201)
        if csosn in ['101', '201'] and produto_fiscal.aliquota_icms:
            icms_resultado["AliquotaCredito"] = float(produto_fiscal.aliquota_icms)
            icms_resultado["ValorCredito"] = float(icms_calc.valor)
        
        print(f"   ICMS (CSOSN {csosn}): R$ {float(icms_calc.valor):.2f}")
        print(f"   {icms_calc.observacoes}")
        
    else:
        # Regime Normal - usa CST
        cst_icms = produto_fiscal.cst_icms or "00"
        
        icms_calc = calc.calcular_icms_regime_normal(
            valor_produto=valor_total,
            cst=cst_icms,
            aliquota=produto_fiscal.aliquota_icms
        )
        
        icms_resultado["CodSituacaoTributaria"] = cst_icms
        
        if float(icms_calc.valor) > 0:
            icms_resultado["BaseCalculo"] = float(icms_calc.base_calculo)
            icms_resultado["Aliquota"] = float(icms_calc.aliquota)
            icms_resultado["Valor"] = float(icms_calc.valor)
        
        print(f"   ICMS (CST {cst_icms}): R$ {float(icms_calc.valor):.2f}")
    
    # ==========================================
    # IPI
    # ==========================================
    # Para Simples Nacional, geralmente é não tributado (53)
    # Para Regime Normal, verificar CST do produto
    
    if regime == "SIMPLES_NACIONAL":
        ipi_resultado = {
            "CodSituacaoTributaria": "53",  # Não tributado
            "CodEnquadramento": "999"
        }
        print(f"   IPI: Não tributado (CST 53)")
    else:
        cst_ipi = "53"  # Padrão: não tributado
        ipi_calc = calc.calcular_ipi(
            valor_produto=valor_total,
            cst=cst_ipi
        )
        
        ipi_resultado = {
            "CodSituacaoTributaria": cst_ipi,
            "CodEnquadramento": "999"
        }
        
        if float(ipi_calc.valor) > 0:
            ipi_resultado["Aliquota"] = float(ipi_calc.aliquota)
            ipi_resultado["Valor"] = float(ipi_calc.valor)
        
        print(f"   IPI: R$ {float(ipi_calc.valor):.2f}")
    
    # ==========================================
    # PIS
    # ==========================================
    cst_pis = produto_fiscal.cst_pis or "07"  # Padrão: isento
    
    # Define regime PIS/COFINS
    regime_pis_cofins = "CUMULATIVO" if regime == "SIMPLES_NACIONAL" else "NAO_CUMULATIVO"
    
    pis_calc = calc.calcular_pis(
        valor_produto=valor_total,
        cst=cst_pis,
        regime=regime_pis_cofins,
        aliquota_customizada=produto_fiscal.aliquota_pis
    )
    
    pis_resultado = {
        "CodSituacaoTributaria": cst_pis
    }
    
    if float(pis_calc.valor) > 0:
        pis_resultado["BaseCalculo"] = float(pis_calc.base_calculo)
        pis_resultado["Aliquota"] = float(pis_calc.aliquota)
        pis_resultado["Valor"] = float(pis_calc.valor)
    
    print(f"   PIS (CST {cst_pis}): R$ {float(pis_calc.valor):.2f}")
    
    # ==========================================
    # COFINS
    # ==========================================
    cst_cofins = produto_fiscal.cst_cofins or "07"  # Padrão: isento
    
    cofins_calc = calc.calcular_cofins(
        valor_produto=valor_total,
        cst=cst_cofins,
        regime=regime_pis_cofins,
        aliquota_customizada=produto_fiscal.aliquota_cofins
    )
    
    cofins_resultado = {
        "CodSituacaoTributaria": cst_cofins
    }
    
    if float(cofins_calc.valor) > 0:
        cofins_resultado["BaseCalculo"] = float(cofins_calc.base_calculo)
        cofins_resultado["Aliquota"] = float(cofins_calc.aliquota)
        cofins_resultado["Valor"] = float(cofins_calc.valor)
    
    print(f"   COFINS (CST {cst_cofins}): R$ {float(cofins_calc.valor):.2f}")
    
    # ==========================================
    # TOTAL DE TRIBUTOS
    # ==========================================
    total_tributos = (
        float(icms_calc.valor) +
        float(pis_calc.valor) +
        float(cofins_calc.valor)
    )
    
    print(f"   TOTAL TRIBUTOS: R$ {total_tributos:.2f}")
    print()
    
    return {
        "ICMS": icms_resultado,
        "IPI": ipi_resultado,
        "PIS": pis_resultado,
        "COFINS": cofins_resultado,
        "total_tributos": total_tributos,
        "valor_total": float(valor_total)
    }


def buscar_dados_banco(session, config_id=1, cliente_id=1, produto_fiscal_id=1, transportadora_id=None):
    """
    Busca dados do banco e monta a NF-e COM CÁLCULO AUTOMÁTICO DE IMPOSTOS
    """
    print("=" * 80)
    print("=== BUSCANDO DADOS DO BANCO COM CÁLCULO AUTOMÁTICO DE IMPOSTOS ===")
    print("=" * 80)

    # ============================
    # QUANTIDADE
    # ============================
    quantidade = 8

    # ============================
    # CONFIGURAÇÃO FISCAL (EMITENTE)
    # ============================
    config = session.query(ConfiguracaoFiscal).filter_by(id=config_id).one()

    regime_nome = {
        "1": "Simples Nacional",
        "2": "Regime Normal",
        "3": "MEI"
    }.get(str(config.regime_tributario), "Desconhecido")
    
    print(f"\n📋 EMITENTE:")
    print(f"   Razão Social: {config.razao_social}")
    print(f"   CNPJ: {config.cnpj}")
    print(f"   Regime: {regime_nome} (CRT {config.regime_tributario})")

    # ============================
    # CLIENTE
    # ============================
    cliente = session.query(ClienteFiscal).filter_by(id=cliente_id).one()
    
    # Determinar indicador de IE corretamente
    indicador_ie = determinar_indicador_ie(cliente)
    
    print(f"\n👤 CLIENTE:")
    print(f"   Nome: {cliente.nome_cliente}")
    print(f"   CPF/CNPJ: {cliente.cpf_cnpj}")
    print(f"   Município: {cliente.municipio}/{cliente.uf}")
    print(f"   Indicador IE: {indicador_ie}")
    print(f"   IE: {cliente.inscricao_estadual}")

    # ============================
    # PRODUTO (CORRIGIDO - relacionamento muitos-para-muitos)
    # ============================
    produto_fiscal = session.query(ProdutoFiscal).filter_by(id=produto_fiscal_id).one()
    
    # Carrega os produtos relacionados explicitamente
    session.refresh(produto_fiscal)
    
    if not produto_fiscal.produtos:
        raise ValueError(f"ProdutoFiscal {produto_fiscal_id} não está relacionado a nenhum produto")
    
    produto = produto_fiscal.produtos[0]  # Pega o primeiro produto da lista
    
    print(f"\n📦 PRODUTO:")
    print(f"   Nome: {produto.nome}")
    print(f"   Código: {produto.codigo}")
    print(f"   NCM: {produto_fiscal.codigo_ncm}")
    print(f"   CFOP: {produto_fiscal.cfop}")
    print(f"   CSOSN: {produto_fiscal.csosn}")

    # ============================
    # VALIDAÇÕES FISCAIS
    # ============================
    if str(config.regime_tributario) == "1" and not produto_fiscal.csosn:
        raise ValueError("CSOSN é obrigatório para Simples Nacional")

    if not produto_fiscal.cfop:
        raise ValueError("CFOP é obrigatório")

    # ============================
    # CÁLCULO AUTOMÁTICO DE IMPOSTOS
    # ============================
    impostos = calcular_impostos_produto(
        session=session,
        produto_fiscal_id=produto_fiscal_id,
        quantidade=quantidade,
        config_fiscal_id=config_id
    )

    # ============================
    # TRANSPORTADORA (SE HOUVER)
    # ============================
    transportadora = None
    veiculo = None
    
    if transportadora_id:
        transportadora = session.query(Transportadora).filter_by(id=transportadora_id).first()
        if transportadora:
            veiculo = session.query(VeiculoTransporte).filter_by(
                transportadora_id=transportadora.id
            ).first()
            print(f"\n🚚 TRANSPORTADORA:")
            print(f"   Razão Social: {transportadora.razao_social}")
            if veiculo:
                print(f"   Veículo: {veiculo.placa}/{veiculo.uf}")
        else:
            print("\n⚠️  Transportadora não encontrada, continuando sem dados de transporte")

    # ============================
    # DADOS DO TRANSPORTE
    # ============================
    if transportadora:
        modalidade_frete = transportadora.modalidade_frete or "0"
        
        transporte = {
            "ModalidadeFrete": int(modalidade_frete),
            "Transportadora": {
                "CpfCnpj": transportadora.cnpj or transportadora.cpf or "",
                "NmTransportadora": transportadora.razao_social,
                "Ie": transportadora.inscricao_estadual or "",
                "Endereco": {
                    "Logradouro": transportadora.logradouro or "",
                    "Numero": transportadora.numero or "",
                    "Complemento": transportadora.complemento or "",
                    "Bairro": transportadora.bairro or "",
                    "Municipio": transportadora.municipio or "",
                    "Uf": transportadora.uf or "",
                    "Cep": transportadora.cep or ""
                }
            }
        }
        
        # Adiciona veículo se disponível
        veiculo_data = {}
        
        if veiculo and veiculo.placa and veiculo.placa.strip():
            veiculo_data["Placa"] = veiculo.placa.strip()
        
        if veiculo and veiculo.uf and veiculo.uf.strip():
            veiculo_data["Uf"] = veiculo.uf.strip().upper()
        
        # RNTC
        rntc_to_use = None
        if veiculo and veiculo.rntc and len(str(veiculo.rntc).strip()) >= 8:
            rntc_to_use = str(veiculo.rntc).strip()
        elif transportadora.rntc and len(str(transportadora.rntc).strip()) >= 8:
            rntc_to_use = str(transportadora.rntc).strip()
        
        if rntc_to_use:
            veiculo_data["Rntc"] = rntc_to_use
        
        if veiculo_data:
            transporte["Veiculo"] = veiculo_data
            
    else:
        transporte = {
            "ModalidadeFrete": 9  # Sem frete
        }

    # ============================
    # JSON DA NF-e COM IMPOSTOS CALCULADOS
    # ============================
    dados_nfe = {
        "IdentificadorInterno": f"VENDA-{datetime.now().strftime('%Y%m%d%H%M%S')}",

        "Serie": int(config.serie_nfe),
        "Numero": 0,
        "ModeloDocumento": 55,
        "Finalidade": 1,
        "NaturezaOperacao": "Venda de mercadoria",
        "ConsumidorFinal": True,
        "IndicadorPresenca": 1,
        "CalcularIBPT": False,

        "DataEmissao": datetime.now().isoformat(),
        "DataEntradaSaida": datetime.now().isoformat(),

        # CLIENTE COM INDICADOR IE CORRETO
        "Cliente": {
            "CpfCnpj": cliente.cpf_cnpj,
            "NmCliente": cliente.nome_cliente,
            "IndicadorIe": indicador_ie,
            "Ie": cliente.inscricao_estadual if indicador_ie == 1 else "",
            "Endereco": {
                "Cep": cliente.cep,
                "Logradouro": cliente.logradouro,
                "Numero": cliente.numero,
                "Complemento": cliente.complemento or "",
                "Bairro": cliente.bairro,
                "CodMunicipio": cliente.codigo_municipio,
                "Municipio": cliente.municipio,
                "Uf": cliente.uf,
                "CodPais": cliente.codigo_pais,
                "Pais": cliente.pais
            },
            "Contato": {
                "Telefone": cliente.telefone or "",
                "Email": cliente.email or ""
            }
        },

        "Produtos": [
            {
                "NmProduto": produto.nome,
                "CodProdutoServico": produto.codigo,
                "EAN": produto_fiscal.codigo_ean or "SEM GTIN",
                "NCM": produto_fiscal.codigo_ncm,
                "CFOP": produto_fiscal.cfop,
                "OrigemProduto": int(produto_fiscal.origem or 0),

                "Quantidade": quantidade,
                "UnidadeComercial": produto.unidade.value,
                "ValorUnitario": float(produto.valor_unitario),
                "ValorTotal": impostos["valor_total"],

                # IMPOSTOS CALCULADOS AUTOMATICAMENTE
                "Imposto": {
                    "ICMS": impostos["ICMS"],
                    "IPI": impostos["IPI"],
                    "PIS": impostos["PIS"],
                    "COFINS": impostos["COFINS"]
                }
            }
        ],

        "Pagamentos": [
            {
                "IndicadorPagamento": 0,
                "FormaPagamento": "01",  # Dinheiro
                "VlPago": impostos["valor_total"]
            }
        ],

        "Transporte": transporte
    }

    return dados_nfe, config, impostos


def criar_html_danfe(retorno, config, output_dir, chave_nfe, data_atual):
    """Cria um HTML visualizável da NF-e"""
    try:
        # Dados formatados
        valor_total = retorno.get("Detalhes", {}).get("valorNf", 0)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NF-e {chave_nfe}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    line-height: 1.4;
                    background-color: #f5f5f5;
                    padding: 20px;
                }}
                
                .danfe-container {{
                    max-width: 210mm;
                    margin: 0 auto;
                    background: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    padding: 10mm;
                }}
                
                .header {{
                    text-align: center;
                    border: 3px double #000;
                    padding: 10px;
                    margin-bottom: 15px;
                }}
                
                .header h1 {{
                    font-size: 16px;
                    color: #0066cc;
                    margin-bottom: 5px;
                }}
                
                .header h2 {{
                    font-size: 14px;
                    color: #333;
                    margin-bottom: 10px;
                }}
                
                .section {{
                    border: 1px solid #000;
                    margin-bottom: 10px;
                    page-break-inside: avoid;
                }}
                
                .section-title {{
                    background-color: #e0e0e0;
                    padding: 3px 5px;
                    font-weight: bold;
                    border-bottom: 1px solid #000;
                }}
                
                .section-content {{
                    padding: 5px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 5px;
                }}
                
                .field {{
                    margin-bottom: 3px;
                }}
                
                .label {{
                    font-weight: bold;
                    display: inline-block;
                    width: 120px;
                }}
                
                .value {{
                    display: inline-block;
                }}
                
                .produtos-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 5px;
                }}
                
                .produtos-table th,
                .produtos-table td {{
                    border: 1px solid #000;
                    padding: 3px;
                    text-align: left;
                    font-size: 10px;
                }}
                
                .produtos-table th {{
                    background-color: #f0f0f0;
                }}
                
                .totais {{
                    text-align: right;
                    margin-top: 10px;
                    padding: 10px;
                    border-top: 2px solid #000;
                    font-weight: bold;
                }}
                
                .assinatura {{
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #000;
                    text-align: center;
                }}
                
                .qrcode-placeholder {{
                    width: 100px;
                    height: 100px;
                    border: 1px dashed #000;
                    margin: 10px auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #666;
                }}
                
                @media print {{
                    body {{
                        background: white;
                        padding: 0;
                    }}
                    
                    .danfe-container {{
                        box-shadow: none;
                        padding: 0;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="danfe-container">
                <!-- Cabeçalho -->
                <div class="header">
                    <h1>DANFE - Documento Auxiliar da Nota Fiscal Eletrônica</h1>
                    <h2>NF-e Nº {retorno.get('Numero', 'N/A')} - Série {retorno.get('Serie', 'N/A')}</h2>
                    <p><strong>Chave de Acesso:</strong> {chave_nfe}</p>
                    <p><strong>Ambiente:</strong> {retorno.get('DsTipoAmbiente', 'N/A')} - {retorno.get('DsStatusRespostaSefaz', 'N/A')}</p>
                </div>
                
                <!-- Emitente -->
                <div class="section">
                    <div class="section-title">EMITENTE</div>
                    <div class="section-content">
                        <div class="field">
                            <span class="label">Razão Social:</span>
                            <span class="value">{config.razao_social}</span>
                        </div>
                        <div class="field">
                            <span class="label">CNPJ:</span>
                            <span class="value">{config.cnpj}</span>
                        </div>
                        <div class="field">
                            <span class="label">IE:</span>
                            <span class="value">{config.inscricao_estadual or 'N/A'}</span>
                        </div>
                        <div class="field">
                            <span class="label">Endereço:</span>
                            <span class="value">{config.logradouro}, {config.numero}</span>
                        </div>
                        <div class="field">
                            <span class="label">Bairro:</span>
                            <span class="value">{config.bairro}</span>
                        </div>
                        <div class="field">
                            <span class="label">Município:</span>
                            <span class="value">{config.municipio}/{config.uf}</span>
                        </div>
                        <div class="field">
                            <span class="label">CEP:</span>
                            <span class="value">{config.cep}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Dados da NF-e -->
                <div class="section">
                    <div class="section-title">DADOS DA NOTA FISCAL</div>
                    <div class="section-content">
                        <div class="field">
                            <span class="label">Número:</span>
                            <span class="value">{retorno.get('Numero', 'N/A')}</span>
                        </div>
                        <div class="field">
                            <span class="label">Série:</span>
                            <span class="value">{retorno.get('Serie', 'N/A')}</span>
                        </div>
                        <div class="field">
                            <span class="label">Data Emissão:</span>
                            <span class="value">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</span>
                        </div>
                        <div class="field">
                            <span class="label">Protocolo:</span>
                            <span class="value">{retorno.get('NumeroProtocolo', 'N/A')}</span>
                        </div>
                        <div class="field">
                            <span class="label">Natureza:</span>
                            <span class="value">Venda de mercadoria</span>
                        </div>
                    </div>
                </div>
                
                <!-- Valores -->
                <div class="section">
                    <div class="section-title">VALORES</div>
                    <div class="section-content">
                        <div class="field">
                            <span class="label">Valor Total:</span>
                            <span class="value">R$ {valor_total:,.2f}</span>
                        </div>
                        <div class="field">
                            <span class="label">ICMS:</span>
                            <span class="value">R$ {retorno.get('Detalhes', {{}}).get('valorIcms', 0):,.2f}</span>
                        </div>
                        <div class="field">
                            <span class="label">PIS:</span>
                            <span class="value">R$ {retorno.get('Detalhes', {{}}).get('valorPis', 0):,.2f}</span>
                        </div>
                        <div class="field">
                            <span class="label">COFINS:</span>
                            <span class="value">R$ {retorno.get('Detalhes', {{}}).get('valorCofins', 0):,.2f}</span>
                        </div>
                        <div class="field">
                            <span class="label">IPI:</span>
                            <span class="value">R$ {retorno.get('Detalhes', {{}}).get('valorIpi', 0):,.2f}</span>
                        </div>
                    </div>
                </div>
                
                <!-- QR Code Placeholder -->
                <div class="section">
                    <div class="section-title">CONSULTA PÚBLICA</div>
                    <div style="text-align: center; padding: 10px;">
                        <div class="qrcode-placeholder">
                            [QR CODE]
                        </div>
                        <p>Consulta em: https://portalsped.fazenda.mg.gov.br/portalnfce/</p>
                        <p>Chave: {chave_nfe}</p>
                    </div>
                </div>
                
                <!-- Totais -->
                <div class="totais">
                    <p>TOTAL DA NOTA FISCAL: <strong>R$ {valor_total:,.2f}</strong></p>
                </div>
                
                <!-- Assinatura -->
                <div class="assinatura">
                    <p>___________________________________________</p>
                    <p>Documento gerado automaticamente</p>
                    <p>NF-e autorizada pela SEFAZ</p>
                    <p>Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
            </div>
            
            <script>
                // Adiciona funcionalidade de impressão
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('DANFE HTML carregado para NF-e {chave_nfe}');
                }});
            </script>
        </body>
        </html>
        """
        
        html_filename = f"DANFE_{chave_nfe}_{data_atual}.html"
        html_path = os.path.join(output_dir, html_filename)
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ HTML visualizável salvo: {html_path}")
        
    except Exception as e:
        print(f"⚠️  Erro ao criar HTML: {e}")


def criar_resumo_txt(retorno, config, output_dir, chave_nfe, data_atual):
    """Cria um arquivo TXT com resumo da NF-e"""
    try:
        txt_content = f"""
        ========================================================
        RESUMO DA NOTA FISCAL ELETRÔNICA
        ========================================================
        
        CHAVE DE ACESSO: {chave_nfe}
        NÚMERO: {retorno.get('Numero', 'N/A')}
        SÉRIE: {retorno.get('Serie', 'N/A')}
        PROTOCOLO: {retorno.get('NumeroProtocolo', 'N/A')}
        DATA EMISSÃO: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        AMBIENTE: {retorno.get('DsTipoAmbiente', 'N/A')}
        STATUS: {retorno.get('DsStatusRespostaSefaz', 'N/A')}
        
        --------------------------------------------------------
        EMITENTE
        --------------------------------------------------------
        Razão Social: {config.razao_social}
        CNPJ: {config.cnpj}
        IE: {config.inscricao_estadual or 'N/A'}
        Endereço: {config.logradouro}, {config.numero}
        Bairro: {config.bairro}
        Município: {config.municipio}/{config.uf}
        CEP: {config.cep}
        
        --------------------------------------------------------
        VALORES
        --------------------------------------------------------
        Valor Total NF: R$ {retorno.get('Detalhes', {{}}).get('valorNf', 0):,.2f}
        Valor ICMS: R$ {retorno.get('Detalhes', {{}}).get('valorIcms', 0):,.2f}
        Valor PIS: R$ {retorno.get('Detalhes', {{}}).get('valorPis', 0):,.2f}
        Valor COFINS: R$ {retorno.get('Detalhes', {{}}).get('valorCofins', 0):,.2f}
        Valor IPI: R$ {retorno.get('Detalhes', {{}}).get('valorIpi', 0):,.2f}
        
        --------------------------------------------------------
        INFORMAÇÕES DE CONSULTA
        --------------------------------------------------------
        URL: https://portalsped.fazenda.mg.gov.br/portalnfce/
        Chave para consulta: {chave_nfe}
        
        --------------------------------------------------------
        ARQUIVOS GERADOS
        --------------------------------------------------------
        XML: NF-e_{chave_nfe}_{data_atual}.xml
        PDF: DANFE_{chave_nfe}_{data_atual}.pdf
        HTML: DANFE_{chave_nfe}_{data_atual}.html
        JSON: NF-e_{chave_nfe}_{data_atual}_dados.json
        TXT: RESUMO_{chave_nfe}_{data_atual}.txt
        
        ========================================================
        Documento gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        ========================================================
        """
        
        txt_filename = f"RESUMO_{chave_nfe}_{data_atual}.txt"
        txt_path = os.path.join(output_dir, txt_filename)
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        print(f"✅ Resumo TXT salvo: {txt_path}")
        
    except Exception as e:
        print(f"⚠️  Erro ao criar resumo TXT: {e}")


def processar_resposta_nfe(response, config):
    """
    Processa a resposta da NF-e e gera documentos FORMATADOS corretamente
    """
    print("\n" + "=" * 80)
    print("📄 PROCESSANDO RESPOSTA DA NF-e - FORMATANDO DOCUMENTOS")
    print("=" * 80)
    
    # Cria diretório para os arquivos
    output_dir = "./notas_fiscais"
    os.makedirs(output_dir, exist_ok=True)
    
    retorno = response.get("data", {}).get("ReturnNF", {})
    
    if retorno.get("Ok"):
        chave_nfe = retorno.get("ChaveNF")
        numero_nfe = retorno.get("Numero")
        data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. SALVAR XML FORMATADO
        xml_base64 = response.get("data", {}).get("Base64Xml")
        if xml_base64:
            try:
                # Decodifica base64
                xml_bytes = base64.b64decode(xml_base64)
                xml_str = xml_bytes.decode('utf-8')
                
                # Formata o XML para melhor legibilidade
                try:
                    dom = xml.dom.minidom.parseString(xml_str)
                    xml_formatado = dom.toprettyxml(indent="  ")
                except:
                    # Se não conseguir parsear, usa o original
                    xml_formatado = xml_str
                
                # Nome do arquivo
                xml_filename = f"NF-e_{chave_nfe}_{data_atual}.xml"
                xml_path = os.path.join(output_dir, xml_filename)
                
                # Salva o XML formatado
                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_formatado)
                
                print(f"✅ XML formatado salvo: {xml_path}")
                print(f"   Tamanho: {os.path.getsize(xml_path)} bytes")
                
                # Também salva o XML original (binário)
                xml_bin_filename = f"NF-e_{chave_nfe}_{data_atual}_original.xml"
                xml_bin_path = os.path.join(output_dir, xml_bin_filename)
                with open(xml_bin_path, "wb") as f:
                    f.write(xml_bytes)
                
            except Exception as e:
                print(f"❌ Erro ao processar XML: {e}")
        
        # 2. SALVAR PDF
        pdf_base64 = response.get("data", {}).get("Base64File")
        if pdf_base64:
            try:
                # Decodifica base64
                pdf_bytes = base64.b64decode(pdf_base64)
                
                # Verifica se é um PDF válido
                if pdf_bytes[:4] == b'%PDF':
                    # É um PDF válido
                    pdf_filename = f"DANFE_{chave_nfe}_{data_atual}.pdf"
                    pdf_path = os.path.join(output_dir, pdf_filename)
                    
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_bytes)
                    
                    print(f"✅ PDF salvo: {pdf_path}")
                    print(f"   Tamanho: {os.path.getsize(pdf_path)} bytes")
                else:
                    print("⚠️  PDF inválido - não começa com %PDF")
                    # Tenta salvar mesmo assim
                    pdf_filename = f"DANFE_{chave_nfe}_{data_atual}.pdf"
                    pdf_path = os.path.join(output_dir, pdf_filename)
                    
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_bytes)
                    
                    print(f"⚠️  PDF salvo (possivelmente corrompido): {pdf_path}")
                    
            except Exception as e:
                print(f"❌ Erro ao processar PDF: {e}")
        
        # 3. CRIAR HTML VISUALIZÁVEL
        criar_html_danfe(retorno, config, output_dir, chave_nfe, data_atual)
        
        # 4. CRIAR RESUMO TXT
        criar_resumo_txt(retorno, config, output_dir, chave_nfe, data_atual)
        
        # 5. SALVAR JSON COM DADOS FORMATADOS
        dados_nfe = {
            "chave_acesso": chave_nfe,
            "numero": numero_nfe,
            "serie": retorno.get("Serie"),
            "protocolo": retorno.get("NumeroProtocolo"),
            "data_emissao": datetime.now().isoformat(),
            "status": retorno.get("DsStatusRespostaSefaz"),
            "codigo_status": retorno.get("CodStatusRespostaSefaz"),
            "ambiente": retorno.get("DsTipoAmbiente"),
            "emitente": {
                "razao_social": config.razao_social,
                "cnpj": config.cnpj,
                "inscricao_estadual": config.inscricao_estadual,
                "endereco": {
                    "logradouro": config.logradouro,
                    "numero": config.numero,
                    "bairro": config.bairro,
                    "municipio": config.municipio,
                    "uf": config.uf,
                    "cep": config.cep
                }
            },
            "valores": {
                "valor_nf": retorno.get("Detalhes", {}).get("valorNf", 0),
                "valor_icms": retorno.get("Detalhes", {}).get("valorIcms", 0),
                "valor_pis": retorno.get("Detalhes", {}).get("valorPis", 0),
                "valor_cofins": retorno.get("Detalhes", {}).get("valorCofins", 0),
                "valor_ipi": retorno.get("Detalhes", {}).get("valorIpi", 0)
            },
            "informacoes_adicionais": {
                "arquivos_gerados": {
                    "xml": xml_filename if xml_base64 else None,
                    "pdf": pdf_filename if pdf_base64 else None,
                    "html": f"DANFE_{chave_nfe}_{data_atual}.html",
                    "txt": f"RESUMO_{chave_nfe}_{data_atual}.txt",
                    "json": f"NF-e_{chave_nfe}_{data_atual}_dados.json"
                }
            }
        }
        
        json_filename = f"NF-e_{chave_nfe}_{data_atual}_dados.json"
        json_path = os.path.join(output_dir, json_filename)
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dados_nfe, f, indent=2, ensure_ascii=False, sort_keys=True)
        
        print(f"✅ Dados JSON formatados salvos: {json_path}")
        
        print("=" * 80)
        print("🎉 PROCESSAMENTO CONCLUÍDO!")
        print("=" * 80)
        
        return {
            "pdf_path": pdf_path if pdf_base64 else None,
            "xml_path": xml_path if xml_base64 else None,
            "json_path": json_path
        }
    else:
        print("❌ NF-e não autorizada, nenhum documento gerado")
        return None


def verificar_arquivos_gerados():
    """Verifica e lista os arquivos gerados"""
    print("\n" + "=" * 80)
    print("📁 VERIFICANDO ARQUIVOS GERADOS")
    print("=" * 80)
    
    output_dir = "./notas_fiscais"
    
    if not os.path.exists(output_dir):
        print("❌ Diretório não existe")
        return
    
    arquivos = os.listdir(output_dir)
    
    if not arquivos:
        print("❌ Nenhum arquivo encontrado")
        return
    
    print(f"📂 Diretório: {output_dir}")
    print(f"📊 Total de arquivos: {len(arquivos)}")
    print("\nArquivos encontrados:")
    
    for arquivo in sorted(arquivos):
        caminho = os.path.join(output_dir, arquivo)
        tamanho = os.path.getsize(caminho)
        extensao = arquivo.split('.')[-1].upper()
        
        print(f"  📄 {arquivo} ({extensao}, {tamanho:,} bytes)")


def main():
    """
    Função principal - Emite NF-e com cálculo automático de impostos
    """
    app = create_app()

    with app.app_context():
        session = db.session
        
        # Busca dados e calcula impostos automaticamente
        dados_nfe, config, impostos = buscar_dados_banco(
            session, 
            config_id=1,
            cliente_id=1,
            produto_fiscal_id=1,
            transportadora_id=1
        )

        # ============================
        # RESUMO ANTES DE ENVIAR
        # ============================
        print("\n" + "=" * 80)
        print("=== RESUMO DA NF-e ===")
        print("=" * 80)
        print(f"Valor Total dos Produtos: R$ {impostos['valor_total']:.2f}")
        print(f"Total de Tributos:        R$ {impostos['total_tributos']:.2f}")
        print(f"Valor da Nota:            R$ {impostos['valor_total']:.2f}")
        print("=" * 80)

        # Verificar o JSON gerado antes de enviar
        print("\n=== JSON GERADO ===")
        print(json.dumps(dados_nfe, indent=2, ensure_ascii=False))
        print("\n" + "=" * 80 + "\n")

        ambiente = int(config.ambiente or 2)
        ambiente_nome = "PRODUÇÃO" if ambiente == 1 else "HOMOLOGAÇÃO"

        print(f"=== ENVIANDO NF-e PARA {ambiente_nome} ===\n")

        # Envia para a SEFAZ
        response = fiscal_service.emitir_nota(
            dados=dados_nfe,
            ambiente=ambiente
        )

        print("\n=== RESPOSTA DA SEFAZ ===")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print()

        retorno = response.get("data", {}).get("ReturnNF", {})

        if retorno.get("Ok"):
            print("=" * 80)
            print("✅ NF-e AUTORIZADA COM SUCESSO!")
            print("=" * 80)
            print(f"Protocolo: {retorno.get('NumeroProtocolo', 'N/A')}")
            print(f"Chave: {retorno.get('ChaveNF', 'N/A')}")
            print(f"Número: {retorno.get('Numero', 'N/A')}")
            print(f"Status: {retorno.get('DsStatusRespostaSefaz', 'N/A')}")
            print("=" * 80)
            
            # Processa documentos
            arquivos_gerados = processar_resposta_nfe(response, config)
            
            # Verifica arquivos gerados
            verificar_arquivos_gerados()
            
            # Instruções
            print("\n📋 INSTRUÇÕES:")
            print("1. Abra o PDF no navegador ou visualizador de PDF")
            print("2. Para XML, use um editor de texto ou navegador")
            print("3. HTML é uma versão visualizável no navegador")
            print("4. TXT contém um resumo legível")
            print("5. JSON tem todos os dados estruturados")
            
        else:
            print("=" * 80)
            print("❌ ERRO AO AUTORIZAR NF-e")
            print("=" * 80)
            print(f"Código: {retorno.get('CodStatusRespostaSefaz', 'N/A')}")
            print(f"Mensagem: {retorno.get('DsStatusRespostaSefaz', 'N/A')}")
            print("=" * 80)
            raise RuntimeError(retorno.get("DsStatusRespostaSefaz"))


if __name__ == "__main__":
    main()