"""
app/utils/fiscal/helpers.py

Funções auxiliares para preparação e tratamento de dados da NF-e
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from decimal import Decimal
import json
import re


class NFeHelpers:
    """Funções auxiliares para montagem e tratamento de dados da NF-e"""
    
    # ============================================
    # CONSTANTES E MAPEAMENTOS
    # ============================================
    
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
    
    # Mapeamento de códigos de UF (IBGE)
    UF_MAP = {
        '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA',
        '16': 'AP', '17': 'TO', '21': 'MA', '22': 'PI', '23': 'CE',
        '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE',
        '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
        '41': 'PR', '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT',
        '52': 'GO', '53': 'DF'
    }
    
    # Padrões de regex para validação
    CNPJ_PATTERN = re.compile(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    CPF_PATTERN = re.compile(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    CNPJ_CPF_PATTERN = re.compile(r'^\d{11,14}$')  # Apenas dígitos
    CEP_PATTERN = re.compile(r'^\d{5}-?\d{3}$')
    TELEFONE_PATTERN = re.compile(r'^\(\d{2}\)\s?\d{4,5}-?\d{4}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PLACA_PATTERN = re.compile(r'^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$')
    
    # ============================================
    # FUNÇÕES DE FORMATAÇÃO E LIMPEZA
    # ============================================
    
    @staticmethod
    def limpar_cnpj_cpf(documento: str) -> str:
        """Remove formatação de CNPJ/CPF, retorna apenas dígitos"""
        if not documento:
            return ""
        return ''.join(filter(str.isdigit, str(documento)))
    
    @staticmethod
    def formatar_cnpj(cnpj: str) -> str:
        """Formata CNPJ no padrão 00.000.000/0000-00"""
        cnpj_limpo = NFeHelpers.limpar_cnpj_cpf(cnpj)
        if len(cnpj_limpo) != 14:
            return cnpj_limpo
        
        return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"
    
    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        """Formata CPF no padrão 000.000.000-00"""
        cpf_limpo = NFeHelpers.limpar_cnpj_cpf(cpf)
        if len(cpf_limpo) != 11:
            return cpf_limpo
        
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    
    @staticmethod
    def formatar_cep(cep: str) -> str:
        """Formata CEP no padrão 00000-000"""
        cep_limpo = ''.join(filter(str.isdigit, str(cep)))
        if len(cep_limpo) == 8:
            return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
        return cep_limpo
    
    @staticmethod
    def formatar_telefone(telefone: str) -> str:
        """Formata telefone no padrão (00) 0000-0000 ou (00) 00000-0000"""
        telefone_limpo = ''.join(filter(str.isdigit, str(telefone)))
        
        if len(telefone_limpo) == 10:  # Telefone fixo
            return f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
        elif len(telefone_limpo) == 11:  # Celular
            return f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
        
        return telefone_limpo
    
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """
        Normaliza texto: remove espaços extras, converte para maiúsculas
        """
        if not texto:
            return ""
        
        # Remove espaços extras no início e fim
        texto = texto.strip()
        # Remove múltiplos espaços
        texto = ' '.join(texto.split())
        # Converte para maiúsculas
        return texto.upper()
    
    # ============================================
    # FUNÇÕES DE VALIDAÇÃO
    # ============================================
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """Valida CNPJ (formato e dígitos verificadores)"""
        cnpj_limpo = NFeHelpers.limpar_cnpj_cpf(cnpj)
        
        if len(cnpj_limpo) != 14:
            return False
        
        # Elimina CNPJs inválidos conhecidos
        if cnpj_limpo in (c * 14 for c in "0123456789"):
            return False
        
        # Valida primeiro dígito verificador
        peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i in range(12):
            soma += int(cnpj_limpo[i]) * peso[i]
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if digito1 != int(cnpj_limpo[12]):
            return False
        
        # Valida segundo dígito verificador
        peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i in range(13):
            soma += int(cnpj_limpo[i]) * peso[i]
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return digito2 == int(cnpj_limpo[13])
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF (formato e dígitos verificadores)"""
        cpf_limpo = NFeHelpers.limpar_cnpj_cpf(cpf)
        
        if len(cpf_limpo) != 11:
            return False
        
        # Elimina CPFs inválidos conhecidos
        if cpf_limpo in (c * 11 for c in "0123456789"):
            return False
        
        # Valida primeiro dígito verificador
        soma = 0
        peso = 10
        for i in range(9):
            soma += int(cpf_limpo[i]) * peso
            peso -= 1
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if digito1 != int(cpf_limpo[9]):
            return False
        
        # Valida segundo dígito verificador
        soma = 0
        peso = 11
        for i in range(10):
            soma += int(cpf_limpo[i]) * peso
            peso -= 1
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return digito2 == int(cpf_limpo[10])
    
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
    def validar_placa(placa: str) -> bool:
        """Valida formato da placa (antigo ou Mercosul)"""
        placa_limpa = placa.upper().replace('-', '').replace(' ', '')
        return bool(NFeHelpers.PLACA_PATTERN.match(placa_limpa))
    
    # ============================================
    # FUNÇÕES DE TRATAMENTO DE DADOS
    # ============================================
    
    @staticmethod
    def tratar_dados_configuracao(dados: Dict[str, Any]) -> Dict[str, Any]:
        """Trata dados de configuração fiscal antes de salvar"""
        dados_tratados = dados.copy()
        
        # Limpa CNPJ
        if 'cnpj' in dados_tratados:
            cnpj_limpo = NFeHelpers.limpar_cnpj_cpf(dados_tratados['cnpj'])
            if len(cnpj_limpo) == 14 and NFeHelpers.validar_cnpj(cnpj_limpo):
                dados_tratados['cnpj'] = cnpj_limpo
            else:
                raise ValueError(f"CNPJ inválido: {dados_tratados['cnpj']}")
        
        # Limpa CEP
        if 'cep' in dados_tratados:
            dados_tratados['cep'] = NFeHelpers.limpar_cnpj_cpf(dados_tratados['cep'])
        
        # Normaliza textos
        campos_texto = [
            'razao_social', 'nome_fantasia', 'logradouro', 'complemento',
            'bairro', 'municipio', 'email'
        ]
        
        for campo in campos_texto:
            if campo in dados_tratados and dados_tratados[campo]:
                dados_tratados[campo] = NFeHelpers.normalizar_texto(dados_tratados[campo])
        
        # Converte UF para maiúsculas
        if 'uf' in dados_tratados:
            dados_tratados['uf'] = dados_tratados['uf'].upper()[:2]
        
        # Garante valores padrão
        defaults = {
            'serie_nfe': '1',
            'serie_nfce': '2',
            'ambiente': '2',
            'ultimo_numero_nfe': 0,
            'ultimo_numero_nfce': 0,
            'ativo': True
        }
        
        for campo, valor_padrao in defaults.items():
            if campo not in dados_tratados:
                dados_tratados[campo] = valor_padrao
        
        return dados_tratados
    
    @staticmethod
    def tratar_dados_transportadora(dados: Dict[str, Any]) -> Dict[str, Any]:
        """Trata dados de transportadora antes de salvar"""
        dados_tratados = dados.copy()
        
        # Limpa CNPJ/CPF
        if 'cnpj' in dados_tratados and dados_tratados['cnpj']:
            cnpj_limpo = NFeHelpers.limpar_cnpj_cpf(dados_tratados['cnpj'])
            if len(cnpj_limpo) == 14 and NFeHelpers.validar_cnpj(cnpj_limpo):
                dados_tratados['cnpj'] = cnpj_limpo
            else:
                raise ValueError(f"CNPJ inválido: {dados_tratados['cnpj']}")
        
        if 'cpf' in dados_tratados and dados_tratados['cpf']:
            cpf_limpo = NFeHelpers.limpar_cnpj_cpf(dados_tratados['cpf'])
            if len(cpf_limpo) == 11 and NFeHelpers.validar_cpf(cpf_limpo):
                dados_tratados['cpf'] = cpf_limpo
            else:
                raise ValueError(f"CPF inválido: {dados_tratados['cpf']}")
        
        # Limpa CEP
        if 'cep' in dados_tratados and dados_tratados['cep']:
            dados_tratados['cep'] = NFeHelpers.limpar_cnpj_cpf(dados_tratados['cep'])
        
        # Normaliza textos
        campos_texto = [
            'razao_social', 'nome_fantasia', 'logradouro', 'complemento',
            'bairro', 'municipio', 'email', 'rntc'
        ]
        
        for campo in campos_texto:
            if campo in dados_tratados and dados_tratados[campo]:
                dados_tratados[campo] = NFeHelpers.normalizar_texto(dados_tratados[campo])
        
        # Converte UF para maiúsculas
        if 'uf' in dados_tratados:
            dados_tratados['uf'] = dados_tratados['uf'].upper()[:2]
        
        if 'uf_veiculo' in dados_tratados and dados_tratados['uf_veiculo']:
            dados_tratados['uf_veiculo'] = dados_tratados['uf_veiculo'].upper()[:2]
        
        # Formata placa
        if 'placa_veiculo' in dados_tratados and dados_tratados['placa_veiculo']:
            placa = dados_tratados['placa_veiculo'].upper().replace('-', '').replace(' ', '')
            dados_tratados['placa_veiculo'] = placa
        
        # Garante valor padrão
        if 'modalidade_frete' not in dados_tratados:
            dados_tratados['modalidade_frete'] = '0'
        
        return dados_tratados
    
    @staticmethod
    def tratar_dados_veiculo(dados: Dict[str, Any]) -> Dict[str, Any]:
        """Trata dados de veículo de transporte antes de salvar"""
        dados_tratados = dados.copy()
        
        # Formata placa
        if 'placa' in dados_tratados:
            placa = dados_tratados['placa'].upper().replace('-', '').replace(' ', '')
            dados_tratados['placa'] = placa
            
            # Valida placa
            if not NFeHelpers.validar_placa(placa):
                raise ValueError(f"Placa inválida: {placa}")
        
        # Converte UF para maiúsculas
        if 'uf' in dados_tratados:
            dados_tratados['uf'] = dados_tratados['uf'].upper()[:2]
        
        # Normaliza texto
        campos_texto = ['proprietario', 'tipo_veiculo', 'rntc']
        for campo in campos_texto:
            if campo in dados_tratados and dados_tratados[campo]:
                dados_tratados[campo] = NFeHelpers.normalizar_texto(dados_tratados[campo])
        
        # Converte capacidade_carga para string (será convertido para Decimal depois)
        if 'capacidade_carga' in dados_tratados and dados_tratados['capacidade_carga'] is not None:
            try:
                # Garante que seja string para conversão posterior
                dados_tratados['capacidade_carga'] = str(dados_tratados['capacidade_carga'])
            except:
                dados_tratados['capacidade_carga'] = None
        
        # Converte transportadora_id para string (será convertido para int depois)
        if 'transportadora_id' in dados_tratados:
            if dados_tratados['transportadora_id'] == '' or dados_tratados['transportadora_id'] is None:
                dados_tratados['transportadora_id'] = None
            else:
                dados_tratados['transportadora_id'] = str(dados_tratados['transportadora_id'])
        
        return dados_tratados
    
    @staticmethod
    def formatar_dados_para_frontend(dados: Dict[str, Any], tipo: str = 'configuracao') -> Dict[str, Any]:
        """Formata dados para exibição no frontend"""
        dados_formatados = dados.copy()
        
        # Aplica formatação baseada no tipo
        if tipo == 'configuracao':
            if 'cnpj' in dados_formatados:
                dados_formatados['cnpj'] = NFeHelpers.formatar_cnpj(dados_formatados['cnpj'])
            
            if 'cep' in dados_formatados:
                dados_formatados['cep'] = NFeHelpers.formatar_cep(dados_formatados['cep'])
            
            if 'telefone' in dados_formatados:
                dados_formatados['telefone'] = NFeHelpers.formatar_telefone(dados_formatados['telefone'])
        
        elif tipo == 'transportadora':
            if 'cnpj' in dados_formatados and dados_formatados['cnpj']:
                dados_formatados['cnpj'] = NFeHelpers.formatar_cnpj(dados_formatados['cnpj'])
            
            if 'cpf' in dados_formatados and dados_formatados['cpf']:
                dados_formatados['cpf'] = NFeHelpers.formatar_cpf(dados_formatados['cpf'])
            
            if 'cep' in dados_formatados and dados_formatados['cep']:
                dados_formatados['cep'] = NFeHelpers.formatar_cep(dados_formatados['cep'])
            
            if 'telefone' in dados_formatados and dados_formatados['telefone']:
                dados_formatados['telefone'] = NFeHelpers.formatar_telefone(dados_formatados['telefone'])
        
        # Converte datetime para string
        for key, value in dados_formatados.items():
            if isinstance(value, datetime):
                dados_formatados[key] = value.isoformat()
            elif isinstance(value, Decimal):
                dados_formatados[key] = float(value)
        
        return dados_formatados
    
    # ============================================
    # FUNÇÕES ESPECÍFICAS PARA MONTAGEM DE NF-E
    # ============================================
    
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
        """Formata data para o padrão SEFAZ: 2024-08-25T15:00:00-03:00"""
        return data.isoformat()
    
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
        """Gera estrutura simplificada de um produto"""
        valor_total = NFeHelpers.calcular_valor_total_produto(
            quantidade, valor_unitario, desconto
        )
        
        return {
            "NmProduto": NFeHelpers.normalizar_texto(nome),
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
        """Gera estrutura simplificada de um pagamento"""
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
        """Gera estrutura simplificada de cliente"""
        # Determina se é pessoa física ou jurídica
        doc_limpo = NFeHelpers.limpar_cnpj_cpf(cpf_cnpj)
        indicador_ie = 9 if len(doc_limpo) == 11 else 9  # 9=Não Contribuinte
        
        return {
            "CpfCnpj": doc_limpo,
            "NmCliente": NFeHelpers.normalizar_texto(nome),
            "IndicadorIe": indicador_ie,
            "Ie": "",
            "IsUf": "",
            "Endereco": {
                "Cep": NFeHelpers.limpar_cnpj_cpf(cep),
                "Logradouro": NFeHelpers.normalizar_texto(logradouro),
                "Complemento": "",
                "Numero": numero,
                "Bairro": NFeHelpers.normalizar_texto(bairro),
                "CodMunicipio": cod_municipio,
                "Municipio": NFeHelpers.normalizar_texto(municipio),
                "Uf": uf.upper() if uf else "",
                "CodPais": 1058,
                "Pais": "BRASIL"
            },
            "Contato": {
                "Telefone": NFeHelpers.limpar_cnpj_cpf(telefone),
                "Email": email.lower() if email else "",
                "Fax": ""
            }
        }
    
    @staticmethod
    def calcular_totais_nota(produtos: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcula os totais da nota baseado na lista de produtos"""
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
    
    # ============================================
    # FUNÇÕES AUXILIARES
    # ============================================
    
    @staticmethod
    def extrair_uf_por_codigo_municipio(codigo_municipio: str) -> Optional[str]:
        """Extrai UF a partir do código do município (IBGE)"""
        if not codigo_municipio or len(codigo_municipio) < 2:
            return None
        
        uf_code = codigo_municipio[:2]
        return NFeHelpers.UF_MAP.get(uf_code)


# ============================================
# FUNÇÕES DE CONVENIÊNCIA (standalone)
# ============================================

def limpar_cnpj(cnpj: str) -> str:
    """Remove formatação de CNPJ"""
    return NFeHelpers.limpar_cnpj_cpf(cnpj)

def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ no padrão 00.000.000/0000-00"""
    return NFeHelpers.formatar_cnpj(cnpj)

def validar_cnpj(cnpj: str) -> bool:
    """Valida CNPJ (formato e dígitos verificadores)"""
    return NFeHelpers.validar_cnpj(cnpj)

def limpar_cpf(cpf: str) -> str:
    """Remove formatação de CPF"""
    return NFeHelpers.limpar_cnpj_cpf(cpf)

def formatar_cpf(cpf: str) -> str:
    """Formata CPF no padrão 000.000.000-00"""
    return NFeHelpers.formatar_cpf(cpf)

def validar_cpf(cpf: str) -> bool:
    """Valida CPF (formato e dígitos verificadores)"""
    return NFeHelpers.validar_cpf(cpf)

def formatar_cep(cep: str) -> str:
    """Formata CEP no padrão 00000-000"""
    return NFeHelpers.formatar_cep(cep)

def formatar_telefone(telefone: str) -> str:
    """Formata telefone no padrão (00) 0000-0000 ou (00) 00000-0000"""
    return NFeHelpers.formatar_telefone(telefone)

def normalizar_texto(texto: str) -> str:
    """Normaliza texto: remove espaços extras, converte para maiúsculas"""
    return NFeHelpers.normalizar_texto(texto)

