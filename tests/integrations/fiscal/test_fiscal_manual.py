"""
tests/integrations/fiscal/test_fiscal_manual_com_calculo_impostos.py

Versão INTEGRADA com cálculo automático de impostos
"""

from app.integrations.fiscal_api.service import fiscal_service
import json
from datetime import datetime
from decimal import Decimal
from app import create_app, db

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
    
    # Busca produto
    produto = session.query(Produto).filter_by(id=produto_fiscal.produto_id).first()
    if not produto:
        raise ValueError(f"Produto {produto_fiscal.produto_id} não encontrado")
    
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
    
    print(f"\n👤 CLIENTE:")
    print(f"   Nome: {cliente.nome_cliente}")
    print(f"   CPF/CNPJ: {cliente.cpf_cnpj}")
    print(f"   Município: {cliente.municipio}/{cliente.uf}")

    # ============================
    # PRODUTO
    # ============================
    produto_fiscal = session.query(ProdutoFiscal).filter_by(id=produto_fiscal_id).one()
    produto = session.query(Produto).filter_by(id=produto_fiscal.produto_id).one()
    
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

        "Cliente": cliente.to_nfe_dict(),

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
            print(f"Chave: {retorno.get('ChaveAcesso', 'N/A')}")
            print(f"Número: {retorno.get('Numero', 'N/A')}")
            print("=" * 80)
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