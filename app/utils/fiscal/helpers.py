# app/utils/fiscal/helpers.py

"""
Funções auxiliares para preparação de dados da NF-e
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
import json


class NFeHelpers:
    """Funções auxiliares para montagem de NF-e"""
    
    # Códigos de CST ICMS comuns
    CST_ICMS = {
        "TRIBUTADA_INTEGRALMENTE": "00",
        "TRIBUTADA_COM_COBRANCA_POR_ST": "10",
        "COM_REDUCAO_BC": "20",
        "ISENTA_OU_NAO_TRIBUTADA": "40",
        "ISENTA": "41",
        "SUSPENSAO": "50",
        "DIFERIMENTO": "51",
        "ICMS_COBRADO_ANTERIORMENTE_ST": "60",
        "SIMPLES_NACIONAL": "102",
        "SIMPLES_NACIONAL_COM_PERMISSAO_CREDITO": "103",
        "SIMPLES_NACIONAL_ISENTA": "400",
        "SIMPLES_NACIONAL_SUSPENSAO": "500"
    }
    
    # Códigos de CST IPI comuns
    CST_IPI = {
        "ENTRADA_RECUPERACAO_CREDITO": "00",
        "ENTRADA_TRIBUTADA_ALIQUOTA_ZERO": "01",
        "ENTRADA_ISENTA": "02",
        "ENTRADA_NAO_TRIBUTADA": "03",
        "ENTRADA_IMUNE": "04",
        "ENTRADA_COM_SUSPENSAO": "05",
        "SAIDA_TRIBUTADA": "50",
        "SAIDA_TRIBUTADA_ALIQUOTA_ZERO": "51",
        "SAIDA_ISENTA": "52",
        "SAIDA_NAO_TRIBUTADA": "53",
        "SAIDA_IMUNE": "54",
        "SAIDA_COM_SUSPENSAO": "55"
    }
    
    # Códigos de CST PIS/COFINS comuns
    CST_PIS_COFINS = {
        "OPERACAO_TRIBUTAVEL_CUMULATIVO": "01",
        "OPERACAO_TRIBUTAVEL_NAO_CUMULATIVO": "02",
        "OPERACAO_TRIBUTAVEL_ALIQUOTA_ZERO": "04",
        "OPERACAO_TRIBUTAVEL_ST": "05",
        "OPERACAO_TRIBUTAVEL_ALIQUOTA_ZERO_ST": "06",
        "OPERACAO_ISENTA": "07",
        "OPERACAO_SEM_INCIDENCIA": "08",
        "OPERACAO_COM_SUSPENSAO": "09"
    }
    
    # Formas de pagamento
    FORMAS_PAGAMENTO = {
        "DINHEIRO": "01",
        "CHEQUE": "02",
        "CARTAO_CREDITO": "03",
        "CARTAO_DEBITO": "04",
        "CREDITO_LOJA": "05",
        "VALE_ALIMENTACAO": "10",
        "VALE_REFEICAO": "11",
        "VALE_PRESENTE": "12",
        "VALE_COMBUSTIVEL": "13",
        "DUPLICATA_MERCANTIL": "14",
        "BOLETO_BANCARIO": "15",
        "SEM_PAGAMENTO": "90",
        "OUTROS": "99"
    }
    
    # Modalidades de frete
    MODALIDADE_FRETE = {
        "EMITENTE": 0,
        "DESTINATARIO": 1,
        "TERCEIROS": 2,
        "PROPRIO_EMITENTE": 3,
        "PROPRIO_DESTINATARIO": 4,
        "SEM_FRETE": 9
    }
    
    # Indicadores de presença
    INDICADOR_PRESENCA = {
        "NAO_SE_APLICA": 0,
        "PRESENCIAL": 1,
        "INTERNET": 2,
        "TELEATENDIMENTO": 3,
        "ENTREGA_DOMICILIO": 4,
        "PRESENCIAL_FORA_ESTABELECIMENTO": 5,
        "NAO_PRESENCIAL_OUTROS": 9
    }
    
    @staticmethod
    def formatar_cpf_cnpj(documento: str) -> str:
        """Remove formatação de CPF/CNPJ"""
        return ''.join(filter(str.isdigit, documento))
    
    @staticmethod
    def formatar_cep(cep: str) -> str:
        """Remove formatação de CEP"""
        return ''.join(filter(str.isdigit, cep))
    
    @staticmethod
    def formatar_telefone(telefone: str) -> str:
        """Remove formatação de telefone"""
        return ''.join(filter(str.isdigit, telefone))
    
    @staticmethod
    def calcular_valor_total_produto(
        quantidade: float,
        valor_unitario: float,
        desconto: float = 0,
        frete: float = 0,
        seguro: float = 0,
        outras_despesas: float = 0
    ) -> float:
        """Calcula o valor total do produto"""
        valor_bruto = quantidade * valor_unitario
        valor_total = valor_bruto - desconto + frete + seguro + outras_despesas
        return round(valor_total, 2)
    
    @staticmethod
    def formatar_data_sefaz(data: datetime) -> str:
        """
        Formata data para o padrão SEFAZ
        Formato: 2024-08-25T15:00:00-03:00
        """
        return data.isoformat()
    
    @staticmethod
    def validar_ncm(ncm: str) -> bool:
        """Valida formato do NCM (8 dígitos)"""
        ncm_limpo = ''.join(filter(str.isdigit, ncm))
        return len(ncm_limpo) == 8
    
    @staticmethod
    def validar_cfop(cfop: str) -> bool:
        """Valida formato do CFOP (4 dígitos)"""
        cfop_limpo = ''.join(filter(str.isdigit, str(cfop)))
        return len(cfop_limpo) == 4
    
    @staticmethod
    def gerar_produto_simples(
        nome: str,
        codigo: str,
        quantidade: float,
        valor_unitario: float,
        cfop: int,
        ncm: str = "",
        unidade: str = "UN",
        desconto: float = 0,
        cst_icms: str = "102",
        cst_pis: str = "07",
        cst_cofins: str = "07",
        aliquota_icms: float = 0,
        aliquota_pis: float = 0,
        aliquota_cofins: float = 0
    ) -> Dict[str, Any]:
        """
        Gera estrutura simplificada de um produto
        Útil para operações básicas
        """
        valor_total = NFeHelpers.calcular_valor_total_produto(
            quantidade, valor_unitario, desconto
        )
        
        return {
            "NmProduto": nome,
            "CodProdutoServico": codigo,
            "EAN": "",
            "NCM": ncm,
            "CEST": "",
            "Quantidade": quantidade,
            "UnidadeComercial": unidade,
            "ValorDesconto": desconto,
            "ValorUnitario": valor_unitario,
            "ValorTotal": valor_total,
            "ValorSeguro": 0,
            "ValorFrete": 0,
            "ValorOutrasDespesas": 0,
            "CFOP": cfop,
            "NItemPed": "",
            "xPed": "",
            "InformacaoAdicional": "",
            "OrigemProduto": 0,
            "CodTributação": "",
            "Imposto": {
                "ICMS": {
                    "CodSituacaoTributaria": cst_icms,
                    "AliquotaICMS": aliquota_icms,
                    "AliquotaICMSST": 0,
                    "AliquotaMVA": 0,
                    "AliquotaCredito": 0,
                    "RedICMS": 0,
                    "RedICMSST": "0.00"
                },
                "IPI": {
                    "CodEnquadramento": "",
                    "CodSituacaoTributaria": "",
                    "Aliquota": 0,
                    "ValorIpiDevolvido": 0,
                    "PercentualMercadoriaDevolvida": 0
                },
                "PIS": {
                    "CodSituacaoTributaria": cst_pis,
                    "Aliquota": aliquota_pis
                },
                "COFINS": {
                    "CodSituacaoTributaria": cst_cofins,
                    "Aliquota": aliquota_cofins
                },
                "IBSCBS": {
                    "CodClassificacaoTributaria": "",
                    "BaseCalculo": 0,
                    "AliquotaIBSUF": 0,
                    "AliquotaIBSMun": 0,
                    "AliquotaCBS": 0
                }
            },
            "Combustivel": {
                "CodProdutoANP": "",
                "DescricaoProdutoANP": "",
                "UFConsumo": ""
            }
        }
    
    @staticmethod
    def gerar_pagamento_simples(
        forma_pagamento: str,
        valor: float,
        descricao: str = "",
        troco: float = 0
    ) -> Dict[str, Any]:
        """
        Gera estrutura simplificada de um pagamento
        """
        return {
            "IndicadorPagamento": 0,  # 0=Pagamento à vista, 1=Pagamento à prazo
            "Descricao": descricao or f"Pagamento - {forma_pagamento}",
            "FormaPagamento": forma_pagamento,
            "VlPago": valor,
            "VlTroco": troco,
            "TipoIntegracao": False,
            "CNPJCredenciadora": "",
            "BandeiraOperadora": "",
            "NumeroAutorizacao": ""
        }
    
    @staticmethod
    def gerar_cliente_simples(
        cpf_cnpj: str,
        nome: str,
        cep: str = "",
        logradouro: str = "",
        numero: str = "",
        bairro: str = "",
        municipio: str = "",
        uf: str = "",
        cod_municipio: str = "",
        email: str = "",
        telefone: str = ""
    ) -> Dict[str, Any]:
        """
        Gera estrutura simplificada de cliente
        """
        # Determina se é pessoa física ou jurídica
        doc_limpo = NFeHelpers.formatar_cpf_cnpj(cpf_cnpj)
        indicador_ie = 9 if len(doc_limpo) == 11 else 9  # 9=Não Contribuinte
        
        return {
            "CpfCnpj": doc_limpo,
            "NmCliente": nome,
            "IndicadorIe": indicador_ie,
            "Ie": "",
            "IsUf": "",
            "Endereco": {
                "Cep": NFeHelpers.formatar_cep(cep),
                "Logradouro": logradouro,
                "Complemento": "",
                "Numero": numero,
                "Bairro": bairro,
                "CodMunicipio": cod_municipio,
                "Municipio": municipio,
                "Uf": uf.upper() if uf else "",
                "CodPais": 1058,
                "Pais": "BRASIL"
            },
            "Contato": {
                "Telefone": NFeHelpers.formatar_telefone(telefone),
                "Email": email,
                "Fax": ""
            }
        }
    
    @staticmethod
    def calcular_totais_nota(produtos: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcula os totais da nota baseado na lista de produtos
        """
        total_produtos = 0
        total_desconto = 0
        total_frete = 0
        total_seguro = 0
        total_outras_despesas = 0
        
        for produto in produtos:
            total_produtos += produto.get("ValorTotal", 0)
            total_desconto += produto.get("ValorDesconto", 0)
            total_frete += produto.get("ValorFrete", 0)
            total_seguro += produto.get("ValorSeguro", 0)
            total_outras_despesas += produto.get("ValorOutrasDespesas", 0)
        
        total_nota = total_produtos + total_frete + total_seguro + total_outras_despesas
        
        return {
            "total_produtos": round(total_produtos, 2),
            "total_desconto": round(total_desconto, 2),
            "total_frete": round(total_frete, 2),
            "total_seguro": round(total_seguro, 2),
            "total_outras_despesas": round(total_outras_despesas, 2),
            "total_nota": round(total_nota, 2)
        }


# # Exemplo de uso
# if __name__ == "__main__":
#     # Exemplo de criação de produto simplificado
#     produto = NFeHelpers.gerar_produto_simples(
#         nome="Mouse Gamer RGB",
#         codigo="MOUSE001",
#         quantidade=2,
#         valor_unitario=89.90,
#         cfop=5102,
#         ncm="84716060"
#     )
    
#     # Exemplo de criação de cliente simplificado
#     cliente = NFeHelpers.gerar_cliente_simples(
#         cpf_cnpj="123.456.789-00",
#         nome="João da Silva",
#         cep="30112-000",
#         logradouro="Rua Exemplo",
#         numero="123",
#         bairro="Centro",
#         municipio="Belo Horizonte",
#         uf="MG",
#         email="joao@email.com",
#         telefone="(31) 3333-4444"
#     )
    
#     print(f"Helpers carregados com sucesso!\n{json.dumps(produto, indent=2, ensure_ascii=False)}\n{json.dumps(cliente, indent=2, ensure_ascii=False)}")