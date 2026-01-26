# app/utils/fiscal/nfe_template.py

"""
Template para geração de payload de NF-e/NFC-e
Baseado na documentação da API Brasil NFe
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class NFeTemplate:
    """
    Template completo para geração de NF-e/NFC-e.
    Todos os campos são mantidos na estrutura, mesmo quando vazios.
    """
    
    @staticmethod
    def gerar_payload(
        # Dados principais da nota
        serie: Optional[int] = None,
        numero: Optional[int] = None,
        lote: Optional[int] = None,
        codigo: Optional[str] = "",
        data_entrada_saida: Optional[str] = None,
        data_emissao: Optional[str] = None,
        justificativa: str = "",
        nf_referencia: Optional[List[str]] = None,
        indicador_presenca: int = 1,
        indicador_intermediador: bool = False,
        consumidor_final: bool = True,
        calcular_ibpt: bool = True,
        natureza_operacao: str = "",
        modelo_documento: int = 55,
        finalidade: int = 1,
        tipo_ambiente: str = "2",
        observacao: str = "",
        observacao_fisco: str = "",
        identificador_interno: str = "",
        
        # Dados do Cliente
        cliente: Optional[Dict[str, Any]] = None,
        
        # Produtos
        produtos: Optional[List[Dict[str, Any]]] = None,
        
        # Pagamentos
        pagamentos: Optional[List[Dict[str, Any]]] = None,
        
        # Cobrança
        cobranca: Optional[Dict[str, Any]] = None,
        
        # Transporte
        transporte: Optional[Dict[str, Any]] = None,
        
        # Entrega
        entrega: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera o payload completo para envio à API Brasil NFe.
        
        Args:
            Todos os parâmetros conforme documentação da API
            
        Returns:
            Dict contendo a estrutura completa do payload
        """
        
        # Data/hora atual se não fornecida
        if not data_emissao:
            data_emissao = datetime.now().isoformat()
        if not data_entrada_saida:
            data_entrada_saida = datetime.now().isoformat()
        
        payload = {
            "Serie": serie,
            "Numero": numero,
            "Lote": lote,
            "Codigo": codigo,
            "DataEntradaSaida": data_entrada_saida,
            "DataEmissao": data_emissao,
            "Justificativa": justificativa,
            "NFReferencia": nf_referencia or [],
            "IndicadorPresenca": indicador_presenca,
            "IndicadorIntermediador": indicador_intermediador,
            "ConsumidorFinal": consumidor_final,
            "CalcularIBPT": calcular_ibpt,
            "NaturezaOperacao": natureza_operacao,
            "ModeloDocumento": modelo_documento,
            "Finalidade": finalidade,
            "TipoAmbiente": tipo_ambiente,
            "Observacao": observacao,
            "ObservacaoFisco": observacao_fisco,
            "IdentificadorInterno": identificador_interno,
            "Cliente": NFeTemplate._montar_cliente(cliente),
            "Produtos": NFeTemplate._montar_produtos(produtos),
            "Pagamentos": NFeTemplate._montar_pagamentos(pagamentos),
            "Cobranca": NFeTemplate._montar_cobranca(cobranca),
            "Transporte": NFeTemplate._montar_transporte(transporte),
            "Entrega": NFeTemplate._montar_entrega(entrega)
        }
        
        return payload
    
    @staticmethod
    def _montar_cliente(dados: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Monta estrutura do Cliente mantendo todos os campos"""
        if not dados:
            dados = {}
        
        return {
            "CpfCnpj": dados.get("CpfCnpj", ""),
            "NmCliente": dados.get("NmCliente", ""),
            "IndicadorIe": dados.get("IndicadorIe", 9),
            "Ie": dados.get("Ie", ""),
            "IsUf": dados.get("IsUf", ""),
            "Endereco": {
                "Cep": dados.get("Endereco", {}).get("Cep", ""),
                "Logradouro": dados.get("Endereco", {}).get("Logradouro", ""),
                "Complemento": dados.get("Endereco", {}).get("Complemento", ""),
                "Numero": dados.get("Endereco", {}).get("Numero", ""),
                "Bairro": dados.get("Endereco", {}).get("Bairro", ""),
                "CodMunicipio": dados.get("Endereco", {}).get("CodMunicipio", ""),
                "Municipio": dados.get("Endereco", {}).get("Municipio", ""),
                "Uf": dados.get("Endereco", {}).get("Uf", ""),
                "CodPais": dados.get("Endereco", {}).get("CodPais", 1058),
                "Pais": dados.get("Endereco", {}).get("Pais", "BRASIL")
            },
            "Contato": {
                "Telefone": dados.get("Contato", {}).get("Telefone", ""),
                "Email": dados.get("Contato", {}).get("Email", ""),
                "Fax": dados.get("Contato", {}).get("Fax", "")
            }
        }
    
    @staticmethod
    def _montar_produtos(produtos: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Monta lista de produtos mantendo todos os campos"""
        if not produtos:
            return []
        
        lista_produtos = []
        for prod in produtos:
            produto = {
                "NmProduto": prod.get("NmProduto", ""),
                "CodProdutoServico": prod.get("CodProdutoServico", ""),
                "EAN": prod.get("EAN", ""),
                "NCM": prod.get("NCM", ""),
                "CEST": prod.get("CEST", ""),
                "Quantidade": prod.get("Quantidade", 0),
                "UnidadeComercial": prod.get("UnidadeComercial", "UN"),
                "ValorDesconto": prod.get("ValorDesconto", 0),
                "ValorUnitario": prod.get("ValorUnitario", 0),
                "ValorTotal": prod.get("ValorTotal", 0),
                "ValorSeguro": prod.get("ValorSeguro", 0),
                "ValorFrete": prod.get("ValorFrete", 0),
                "ValorOutrasDespesas": prod.get("ValorOutrasDespesas", 0),
                "CFOP": prod.get("CFOP", ""),
                "NItemPed": prod.get("NItemPed", ""),
                "xPed": prod.get("xPed", ""),
                "InformacaoAdicional": prod.get("InformacaoAdicional", ""),
                "OrigemProduto": prod.get("OrigemProduto", 0),
                "CodTributação": prod.get("CodTributação", ""),
                "Imposto": NFeTemplate._montar_impostos(prod.get("Imposto", {})),
                "Combustivel": NFeTemplate._montar_combustivel(prod.get("Combustivel"))
            }
            lista_produtos.append(produto)
        
        return lista_produtos
    
    @staticmethod
    def _montar_impostos(impostos: Dict[str, Any]) -> Dict[str, Any]:
        """Monta estrutura de impostos mantendo todos os campos"""
        return {
            "ICMS": {
                "CodSituacaoTributaria": impostos.get("ICMS", {}).get("CodSituacaoTributaria", ""),
                "AliquotaICMS": impostos.get("ICMS", {}).get("AliquotaICMS", 0),
                "AliquotaICMSST": impostos.get("ICMS", {}).get("AliquotaICMSST", 0),
                "AliquotaMVA": impostos.get("ICMS", {}).get("AliquotaMVA", 0),
                "AliquotaCredito": impostos.get("ICMS", {}).get("AliquotaCredito", 0),
                "RedICMS": impostos.get("ICMS", {}).get("RedICMS", 0),
                "RedICMSST": impostos.get("ICMS", {}).get("RedICMSST", "0.00")
            },
            "IPI": {
                "CodEnquadramento": impostos.get("IPI", {}).get("CodEnquadramento", ""),
                "CodSituacaoTributaria": impostos.get("IPI", {}).get("CodSituacaoTributaria", ""),
                "Aliquota": impostos.get("IPI", {}).get("Aliquota", 0),
                "ValorIpiDevolvido": impostos.get("IPI", {}).get("ValorIpiDevolvido", 0),
                "PercentualMercadoriaDevolvida": impostos.get("IPI", {}).get("PercentualMercadoriaDevolvida", 0)
            },
            "PIS": {
                "CodSituacaoTributaria": impostos.get("PIS", {}).get("CodSituacaoTributaria", ""),
                "Aliquota": impostos.get("PIS", {}).get("Aliquota", 0)
            },
            "COFINS": {
                "CodSituacaoTributaria": impostos.get("COFINS", {}).get("CodSituacaoTributaria", ""),
                "Aliquota": impostos.get("COFINS", {}).get("Aliquota", 0)
            },
            "IBSCBS": {
                "CodClassificacaoTributaria": impostos.get("IBSCBS", {}).get("CodClassificacaoTributaria", ""),
                "BaseCalculo": impostos.get("IBSCBS", {}).get("BaseCalculo", 0),
                "AliquotaIBSUF": impostos.get("IBSCBS", {}).get("AliquotaIBSUF", 0),
                "AliquotaIBSMun": impostos.get("IBSCBS", {}).get("AliquotaIBSMun", 0),
                "AliquotaCBS": impostos.get("IBSCBS", {}).get("AliquotaCBS", 0)
            }
        }
    
    @staticmethod
    def _montar_combustivel(combustivel: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Monta estrutura de combustível mantendo todos os campos"""
        if not combustivel:
            return {
                "CodProdutoANP": "",
                "DescricaoProdutoANP": "",
                "UFConsumo": ""
            }
        
        return {
            "CodProdutoANP": combustivel.get("CodProdutoANP", ""),
            "DescricaoProdutoANP": combustivel.get("DescricaoProdutoANP", ""),
            "UFConsumo": combustivel.get("UFConsumo", "")
        }
    
    @staticmethod
    def _montar_pagamentos(pagamentos: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Monta lista de pagamentos mantendo todos os campos"""
        if not pagamentos:
            return []
        
        lista_pagamentos = []
        for pag in pagamentos:
            pagamento = {
                "IndicadorPagamento": pag.get("IndicadorPagamento", 0),
                "Descricao": pag.get("Descricao", ""),
                "FormaPagamento": pag.get("FormaPagamento", ""),
                "VlPago": pag.get("VlPago", 0),
                "VlTroco": pag.get("VlTroco", 0),
                "TipoIntegracao": pag.get("TipoIntegracao", False),
                "CNPJCredenciadora": pag.get("CNPJCredenciadora", ""),
                "BandeiraOperadora": pag.get("BandeiraOperadora", ""),
                "NumeroAutorizacao": pag.get("NumeroAutorizacao", "")
            }
            lista_pagamentos.append(pagamento)
        
        return lista_pagamentos
    
    @staticmethod
    def _montar_cobranca(cobranca: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Monta estrutura de cobrança mantendo todos os campos"""
        if not cobranca:
            return {
                "Fatura": {
                    "Numero": "",
                    "Valor": 0,
                    "Desconto": 0,
                    "ValorLiquido": 0
                },
                "Parcelas": []
            }
        
        parcelas = []
        for parcela in cobranca.get("Parcelas", []):
            parcelas.append({
                "Vencimento": parcela.get("Vencimento", ""),
                "Valor": parcela.get("Valor", 0)
            })
        
        return {
            "Fatura": {
                "Numero": cobranca.get("Fatura", {}).get("Numero", ""),
                "Valor": cobranca.get("Fatura", {}).get("Valor", 0),
                "Desconto": cobranca.get("Fatura", {}).get("Desconto", 0),
                "ValorLiquido": cobranca.get("Fatura", {}).get("ValorLiquido", 0)
            },
            "Parcelas": parcelas
        }
    
    @staticmethod
    def _montar_transporte(transporte: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Monta estrutura de transporte mantendo todos os campos"""
        if not transporte:
            return {
                "ModalidadeFrete": 0,
                "NmTransportador": "",
                "CNPJ": "",
                "NmMunicipio": "",
                "DsEndereco": "",
                "IE": "",
                "UF": "",
                "Vagao": "",
                "Balsa": "",
                "Veiculo": {
                    "Placa": "",
                    "UF": "",
                    "RNTC": ""
                },
                "Reboque": [],
                "Volumes": []
            }
        
        reboques = []
        for reboque in transporte.get("Reboque", []):
            reboques.append({
                "Placa": reboque.get("Placa", ""),
                "UF": reboque.get("UF", ""),
                "RNTC": reboque.get("RNTC", "")
            })
        
        volumes = []
        for volume in transporte.get("Volumes", []):
            volumes.append({
                "QuantidadeVolume": volume.get("QuantidadeVolume", 0),
                "Especie": volume.get("Especie", ""),
                "Marca": volume.get("Marca", ""),
                "PesoBruto": volume.get("PesoBruto", 0),
                "PesoLiquido": volume.get("PesoLiquido", 0),
                "Lacres": volume.get("Lacres", [])
            })
        
        return {
            "ModalidadeFrete": transporte.get("ModalidadeFrete", 0),
            "NmTransportador": transporte.get("NmTransportador", ""),
            "CNPJ": transporte.get("CNPJ", ""),
            "NmMunicipio": transporte.get("NmMunicipio", ""),
            "DsEndereco": transporte.get("DsEndereco", ""),
            "IE": transporte.get("IE", ""),
            "UF": transporte.get("UF", ""),
            "Vagao": transporte.get("Vagao", ""),
            "Balsa": transporte.get("Balsa", ""),
            "Veiculo": {
                "Placa": transporte.get("Veiculo", {}).get("Placa", ""),
                "UF": transporte.get("Veiculo", {}).get("UF", ""),
                "RNTC": transporte.get("Veiculo", {}).get("RNTC", "")
            },
            "Reboque": reboques,
            "Volumes": volumes
        }
    
    @staticmethod
    def _montar_entrega(entrega: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Monta estrutura de entrega mantendo todos os campos"""
        if not entrega:
            return {
                "CpfCnpj": "",
                "Nome": "",
                "Ie": "",
                "Endereco": {
                    "Cep": "",
                    "Logradouro": "",
                    "Complemento": "",
                    "Numero": "",
                    "Bairro": "",
                    "CodMunicipio": "",
                    "Municipio": "",
                    "Uf": "",
                    "CodPais": 1058,
                    "Pais": "Brasil"
                },
                "Contato": {
                    "Telefone": "",
                    "Email": ""
                }
            }
        
        return {
            "CpfCnpj": entrega.get("CpfCnpj", ""),
            "Nome": entrega.get("Nome", ""),
            "Ie": entrega.get("Ie", ""),
            "Endereco": {
                "Cep": entrega.get("Endereco", {}).get("Cep", ""),
                "Logradouro": entrega.get("Endereco", {}).get("Logradouro", ""),
                "Complemento": entrega.get("Endereco", {}).get("Complemento", ""),
                "Numero": entrega.get("Endereco", {}).get("Numero", ""),
                "Bairro": entrega.get("Endereco", {}).get("Bairro", ""),
                "CodMunicipio": entrega.get("Endereco", {}).get("CodMunicipio", ""),
                "Municipio": entrega.get("Endereco", {}).get("Municipio", ""),
                "Uf": entrega.get("Endereco", {}).get("Uf", ""),
                "CodPais": entrega.get("Endereco", {}).get("CodPais", 1058),
                "Pais": entrega.get("Endereco", {}).get("Pais", "Brasil")
            },
            "Contato": {
                "Telefone": entrega.get("Contato", {}).get("Telefone", ""),
                "Email": entrega.get("Contato", {}).get("Email", "")
            }
        }


# # Exemplo de uso
# if __name__ == "__main__":
#     # Exemplo de geração de payload
#     payload = NFeTemplate.gerar_payload(
#         serie=1,
#         numero=123456,
#         natureza_operacao="Venda de Mercadoria",
#         modelo_documento=55,
#         tipo_ambiente="2",
#         cliente={
#             "CpfCnpj": "12345678000100",
#             "NmCliente": "CLIENTE TESTE LTDA",
#             "Endereco": {
#                 "Cep": "30112000",
#                 "Logradouro": "Rua Exemplo",
#                 "Numero": "123",
#                 "Bairro": "Centro",
#                 "Municipio": "Belo Horizonte",
#                 "Uf": "MG"
#             }
#         },
#         produtos=[
#             {
#                 "NmProduto": "Produto Teste",
#                 "Quantidade": 1,
#                 "ValorUnitario": 100,
#                 "ValorTotal": 100,
#                 "CFOP": 5102
#             }
#         ]
#     )
    
#     print(f"Payload gerado com sucesso!\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
