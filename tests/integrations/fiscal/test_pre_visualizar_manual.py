import sys
import os
import json
import base64

# Ajusta path para importar o app
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.integrations.fiscal_api.service import fiscal_service


def main():
    # ==========================
    # DADOS FAKE – PRÉ-VISUALIZAÇÃO
    # ==========================
    dados_nota = {
        "TipoArquivo": 1,
        "TipoEnvio": 0,
        "Base64Xml": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4NCjx...",
        "mostrarTarjaPreVisualizacao": True,
        "notaFiscal": {
            "TipoAmbiente": 2,
            "ModeloDocumento": 55,
            "nFInfos": [
                {
                    "Serie": 1,
                    "Numero": 123456,
                    "Lote": 20250101,
                    "Codigo": "12345678",
                    "DataEntradaSaida": "2024-08-25T15:00:00Z",
                    "DataEmissao": "2024-08-25T15:00:00Z",
                    "Justificativa": "Emissão em contingência devido a problemas técnicos.",
                    "NFReferencia": ["12345678901234567890123456789012345678901234"],
                    "IndicadorPresenca": 1,
                    "IndicadorIntermediador": False,
                    "ConsumidorFinal": True,
                    "CalcularIBPT": True,
                    "NaturezaOperacao": "Venda de Mercadoria Adquirida ou Recebida de Terceiros",
                    "ModeloDocumento": 55,
                    "Finalidade": 1,
                    "TipoAmbiente": "2",
                    "Observacao": "Documento emitido conforme a legislação vigente.",
                    "ObservacaoFisco": "Informações fiscais complementares.",
                    "IdentificadorInterno": "PEDIDO-12345",
                    "Cliente": {
                        "CpfCnpj": "12345678000100",
                        "NmCliente": "CLIENTE TESTE LTDA",
                        "IndicadorIe": 9,
                        "Ie": "ISENTO",
                        "IsUf": "123456789",
                        "Endereco": {
                            "Cep": "30112000",
                            "Logradouro": "Rua Exemplo, 123",
                            "Complemento": "Sala 101",
                            "Numero": "123",
                            "Bairro": "Centro",
                            "CodMunicipio": "3106200",
                            "Municipio": "Belo Horizonte",
                            "Uf": "MG",
                            "CodPais": 1058,
                            "Pais": "BRASIL"
                        },
                        "Contato": {
                            "Telefone": "3133334444",
                            "Email": "test@example.com",
                            "Fax": "3133335555"
                        }
                    },
                    "Produtos": [
                        {
                            "NmProduto": "Notebook Dell Latitude",
                            "CodProdutoServico": "NBLT001",
                            "EAN": "7891234567890",
                            "NCM": "84713012",
                            "CEST": "1300800",
                            "Quantidade": 1,
                            "UnidadeComercial": "UN",
                            "ValorDesconto": 50,
                            "ValorUnitario": 2500,
                            "ValorTotal": 2500,
                            "ValorSeguro": 0,
                            "ValorFrete": 20,
                            "ValorOutrasDespesas": 0,
                            "CFOP": 5102,
                            "NItemPed": 1,
                            "xPed": "PC0001",
                            "InformacaoAdicional": "Garantia estendida de 1 ano.",
                            "OrigemProduto": 0,
                            "CodTributação": "TRIB-PADRAO",
                            "Imposto": {
                                "ICMS": {
                                    "CodSituacaoTributaria": "102",
                                    "AliquotaICMS": 18,
                                    "AliquotaICMSST": 0,
                                    "AliquotaMVA": 35,
                                    "AliquotaCredito": 0,
                                    "RedICMS": 0,
                                    "RedICMSST": "0.00"
                                },
                                "IPI": {
                                    "CodEnquadramento": "999",
                                    "CodSituacaoTributaria": "53",
                                    "Aliquota": 10,
                                    "ValorIpiDevolvido": 0,
                                    "PercentualMercadoriaDevolvida": 100
                                },
                                "PIS": {
                                    "CodSituacaoTributaria": "07",
                                    "Aliquota": 0.65
                                },
                                "COFINS": {
                                    "CodSituacaoTributaria": "07",
                                    "Aliquota": 3
                                },
                                "IBSCBS": {
                                    "CodClassificacaoTributaria": "000001",
                                    "BaseCalculo": 1000,
                                    "AliquotaIBSUF": 15,
                                    "AliquotaIBSMun": 5,
                                    "AliquotaCBS": 8.5
                                }
                            },
                            "Combustivel": {
                                "CodProdutoANP": "220102001",
                                "DescricaoProdutoANP": "GASOLINA C COMUM",
                                "UFConsumo": "MG"
                            }
                        }
                    ],
                    "Pagamentos": [
                        {
                            "IndicadorPagamento": 0,
                            "Descricao": "Pagamento em Dinheiro",
                            "FormaPagamento": "17",
                            "VlPago": 2470,
                            "VlTroco": 0,
                            "TipoIntegracao": False,
                            "CNPJCredenciadora": "12345678000199",
                            "BandeiraOperadora": "01",
                            "NumeroAutorizacao": "A123456"
                        }
                    ],
                    "Cobranca": {
                        "Fatura": {
                            "Numero": "FAT0001",
                            "Valor": 2500,
                            "Desconto": 50,
                            "ValorLiquido": 2450
                        },
                        "Parcelas": [
                            {
                                "Vencimento": "2024-08-25T15:00:00Z",
                                "Valor": 816.67
                            }
                        ]
                    },
                    "Transporte": {
                        "ModalidadeFrete": 0,
                        "NmTransportador": "Transportadora Expresso Ltda",
                        "CNPJ": "00123456000199",
                        "NmMunicipio": "São Paulo",
                        "DsEndereco": "Rua das Transportadoras, 50",
                        "IE": "123456789012",
                        "UF": "SP",
                        "Vagao": "Vagao123",
                        "Balsa": "BalsaABC",
                        "Veiculo": {
                            "Placa": "ABC1234",
                            "UF": "SP",
                            "RNTC": "99999999"
                        },
                        "Reboque": [
                            {
                                "Placa": "DEF5678",
                                "UF": "MG",
                                "RNTC": "88888888"
                            }
                        ],
                        "Volumes": [
                            {
                                "QuantidadeVolume": 5,
                                "Especie": "CAIXAS",
                                "Marca": "PROD-A",
                                "PesoBruto": 150.5,
                                "PesoLiquido": 145,
                                "Lacres": ["LCRE001"]
                            }
                        ]
                    },
                    "Entrega": {
                        "CpfCnpj": "12345678901",
                        "Nome": "Filial de Entrega",
                        "Ie": "987654321",
                        "Endereco": {
                            "Cep": "30112000",
                            "Logradouro": "Avenida Brasil, 456",
                            "Complemento": "Portaria A",
                            "Numero": "456",
                            "Bairro": "Savassi",
                            "CodMunicipio": "3106200",
                            "Municipio": "Belo Horizonte",
                            "Uf": "MG",
                            "CodPais": 1058,
                            "Pais": "Brasil"
                        },
                        "Contato": {
                            "Telefone": "3133334445",
                            "Email": "test@example.com"
                        }
                    }
                }
            ]
        }
    }

    print("Enviando pré-visualização...\n")

    resposta = fiscal_service.pre_visualizar(
        dados_nota=dados_nota,
        tipo_arquivo=0  # 1=PDF | 0=XML
    )

    print(json.dumps(resposta, indent=2, ensure_ascii=False))

    # ==========================
    # SALVAR PDF (se existir)
    # ==========================
    if resposta.get("success"):
        data = resposta.get("data", {})

        pdf_base64 = (
            data.get("PdfBase64")
            or data.get("PDF")
            or data.get("Arquivo")
        )

        if pdf_base64:
            with open("pre_visualizacao.pdf", "wb") as f:
                f.write(base64.b64decode(pdf_base64))

            print("\nPDF gerado com sucesso: pre_visualizacao.pdf")
        else:
            print("\nResposta OK, mas PDF não encontrado no retorno.")


if __name__ == "__main__":
    main()
