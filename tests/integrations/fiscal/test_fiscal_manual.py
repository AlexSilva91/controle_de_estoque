from app.integrations.fiscal_api.service import fiscal_service
import json

def main():
    # ==============================
    # DADOS FAKE – HOMOLOGAÇÃO
    # ==============================

    dados_fake = {
        "Serie": 1,
        "Numero": 98766,
        "Lote": 20260128,
        "Codigo": "NF98765",
        "DataEntradaSaida": "2026-01-28T10:30:00-03:00",
        "DataEmissao": "2026-01-28T10:30:00-03:00",
        "IndicadorPresenca": 1,
        "IndicadorIntermediador": False,
        "ConsumidorFinal": True,
        "CalcularIBPT": True,
        "NaturezaOperacao": "Venda de mercadoria",
        "ModeloDocumento": 55,
        "Finalidade": 1,
        "Observacao": "Venda realizada conforme pedido interno.",
        "ObservacaoFisco": "Documento emitido em ambiente de homologação.",
        "IdentificadorInterno": "VENDA-2027-0001",
        "Cliente": {
            "CpfCnpj": "12345678910",  # NÃO ALTERADO
            "NmCliente": "João da Silva",
            "IndicadorIe": 9,
            "Ie": "ISENTO",
            "Endereco": {
                "Cep": "30112000",
                "Logradouro": "Rua dos Timbiras",
                "Numero": "1500",
                "Bairro": "Funcionários",
                "CodMunicipio": "3106200",
                "Municipio": "Belo Horizonte",
                "Uf": "MG",
                "CodPais": 1058,
                "Pais": "BRASIL"
            },
            "Contato": {
                "Telefone": "31998887766",
                "Email": "joao.silva@email.com"
            }
        },

        "Produtos": [{
                "NmProduto": "Notebook Dell Inspiron 15",
                "CodProdutoServico": "NOTE-DELL-15",
                "EAN": "SEM GTIN",
                "NCM": "84713012",
                "Quantidade": 1,
                "UnidadeComercial": "UN",
                "ValorUnitario": 3500.00,
                "ValorTotal": 3500.00,
                "CFOP": 5102,
                "OrigemProduto": 0,

                "Imposto": {
                    "ICMS": {
                        "CodSituacaoTributaria": "102"
                    },
                    "IPI": {
                        "CodEnquadramento": "999",
                        "CodSituacaoTributaria": "53"
                    },
                    "PIS": {
                        "CodSituacaoTributaria": "07"
                    },
                    "COFINS": {
                        "CodSituacaoTributaria": "07"
                    }
                }
            }
        ],

        "Pagamentos": [{
                "IndicadorPagamento": 0,
                "FormaPagamento": "03",          # Cartão de Crédito
                "VlPago": 3500.00,

                "Cartao": {
                    "TipoIntegracao": 1,         # 1 = Integrado / 2 = Não integrado
                    "CNPJCredenciadora": "12345678000199",
                    "BandeiraOperadora": "01",   # Visa
                    "NumeroAutorizacao": "CRD123456"
                }
            }
        ],

        "Cobranca": {
            "Fatura": {
                "Numero": "FAT-2026-0001",
                "Valor": 3500.00,
                "ValorLiquido": 3500.00
            },
            "Parcelas": [
                {
                    "Vencimento": "2026-02-28",
                    "Valor": 3500.00
                }
            ]
        },

        "Transporte": {
            "ModalidadeFrete": 9  # Sem frete
        }
    }


    print("=== ENVIANDO NOTA FAKE (HOMOLOGAÇÃO) ===")

    response = fiscal_service.emitir_nota(
        dados=dados_fake,
        ambiente=2  # 2 = Homologação
    )

    print("\n=== RESPOSTA DA API ===")
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
