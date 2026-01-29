"""
app/utils/fiscal/calculo_impostos.py

Funções para cálculo de impostos da NF-e (ICMS, PIS, COFINS, IPI)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ResultadoImposto:
    """Resultado do cálculo de um imposto"""
    base_calculo: Decimal
    aliquota: Decimal
    valor: Decimal
    observacoes: str = ""


class CalculadoraImpostos:
    """Classe para cálculo de impostos da NF-e"""
    
    # ============================================
    # TABELAS DE ALÍQUOTAS PADRÃO
    # ============================================
    
    # Alíquotas de ICMS por UF (interestaduais)
    ALIQUOTA_ICMS_INTERESTADUAL = {
        'SUL_SUDESTE': Decimal('12.00'),  # Exceto ES
        'NORTE_NORDESTE_CO_ES': Decimal('7.00')
    }
    
    # Estados das regiões
    UF_SUL_SUDESTE = ['RS', 'SC', 'PR', 'SP', 'RJ', 'MG']
    UF_NORTE_NORDESTE_CO_ES = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
                                'MA', 'MT', 'MS', 'PA', 'PB', 'PE', 'PI', 'RN', 'RO', 
                                'RR', 'SE', 'TO']
    
    # Alíquotas de PIS e COFINS
    ALIQUOTA_PIS_REGIME_CUMULATIVO = Decimal('0.65')
    ALIQUOTA_PIS_REGIME_NAO_CUMULATIVO = Decimal('1.65')
    ALIQUOTA_COFINS_REGIME_CUMULATIVO = Decimal('3.00')
    ALIQUOTA_COFINS_REGIME_NAO_CUMULATIVO = Decimal('7.60')
    
    # ============================================
    # FUNÇÕES AUXILIARES
    # ============================================
    
    @staticmethod
    def arredondar(valor: Decimal, casas: int = 2) -> Decimal:
        """Arredonda valor com precisão de casas decimais"""
        quantize_value = Decimal(10) ** -casas
        return valor.quantize(quantize_value, rounding=ROUND_HALF_UP)
    
    @staticmethod
    def to_decimal(valor: Any) -> Decimal:
        """Converte valor para Decimal"""
        if isinstance(valor, Decimal):
            return valor
        if valor is None:
            return Decimal('0')
        return Decimal(str(valor))
    
    # ============================================
    # CÁLCULO DE ICMS
    # ============================================
    
    @staticmethod
    def calcular_icms_simples_nacional(
        valor_produto: Decimal,
        cst: str,
        aliquota_credito: Optional[Decimal] = None
    ) -> ResultadoImposto:
        """
        Calcula ICMS para empresas do Simples Nacional
        
        CST Simples Nacional:
        - 101: Tributada com permissão de crédito
        - 102: Tributada sem permissão de crédito
        - 103: Isenção do ICMS
        - 201: Tributada com permissão de crédito e com cobrança do ICMS por ST
        - 202: Tributada sem permissão de crédito e com cobrança do ICMS por ST
        - 203: Isenção do ICMS e com cobrança do ICMS por ST
        - 300: Imune
        - 400: Não tributada
        - 500: ICMS cobrado anteriormente por ST ou por antecipação
        - 900: Outros
        """
        valor_produto = CalculadoraImpostos.to_decimal(valor_produto)
        
        # CSTs que permitem crédito
        if cst in ['101', '201']:
            if aliquota_credito is None:
                aliquota_credito = Decimal('0')
            else:
                aliquota_credito = CalculadoraImpostos.to_decimal(aliquota_credito)
            
            valor_credito = CalculadoraImpostos.arredondar(
                (valor_produto * aliquota_credito) / Decimal('100')
            )
            
            return ResultadoImposto(
                base_calculo=valor_produto,
                aliquota=aliquota_credito,
                valor=valor_credito,
                observacoes=f"Simples Nacional - CST {cst} - Crédito permitido"
            )
        
        # Demais CSTs: sem ICMS
        return ResultadoImposto(
            base_calculo=Decimal('0'),
            aliquota=Decimal('0'),
            valor=Decimal('0'),
            observacoes=f"Simples Nacional - CST {cst} - Sem ICMS"
        )
    
    @staticmethod
    def calcular_icms_regime_normal(
        valor_produto: Decimal,
        cst: str,
        aliquota: Optional[Decimal] = None,
        reducao_bc: Optional[Decimal] = None,
        valor_frete: Optional[Decimal] = None,
        valor_seguro: Optional[Decimal] = None,
        outras_despesas: Optional[Decimal] = None,
        valor_desconto: Optional[Decimal] = None
    ) -> ResultadoImposto:
        """
        Calcula ICMS para empresas no Regime Normal
        
        CST ICMS:
        - 00: Tributada integralmente
        - 10: Tributada e com cobrança do ICMS por substituição tributária
        - 20: Com redução de base de cálculo
        - 30: Isenta ou não tributada e com cobrança do ICMS por ST
        - 40: Isenta
        - 41: Não tributada
        - 50: Suspensão
        - 51: Diferimento
        - 60: ICMS cobrado anteriormente por ST
        - 70: Com redução de BC e cobrança do ICMS por ST
        - 90: Outras
        """
        valor_produto = CalculadoraImpostos.to_decimal(valor_produto)
        valor_frete = CalculadoraImpostos.to_decimal(valor_frete)
        valor_seguro = CalculadoraImpostos.to_decimal(valor_seguro)
        outras_despesas = CalculadoraImpostos.to_decimal(outras_despesas)
        valor_desconto = CalculadoraImpostos.to_decimal(valor_desconto)
        
        # Base de cálculo = Valor Produto + Frete + Seguro + Outras - Desconto
        base_calculo = (
            valor_produto + valor_frete + valor_seguro + 
            outras_despesas - valor_desconto
        )
        
        # CSTs que não tributam ICMS
        if cst in ['40', '41', '50', '51', '60']:
            return ResultadoImposto(
                base_calculo=Decimal('0'),
                aliquota=Decimal('0'),
                valor=Decimal('0'),
                observacoes=f"CST {cst} - Sem tributação de ICMS"
            )
        
        # CSTs com redução de base de cálculo
        if cst in ['20', '70']:
            reducao_bc = CalculadoraImpostos.to_decimal(reducao_bc or 0)
            base_calculo = base_calculo * (Decimal('100') - reducao_bc) / Decimal('100')
        
        # CSTs que tributam
        if cst in ['00', '10', '20', '70', '90']:
            if aliquota is None:
                aliquota = Decimal('0')
            else:
                aliquota = CalculadoraImpostos.to_decimal(aliquota)
            
            valor_icms = CalculadoraImpostos.arredondar(
                (base_calculo * aliquota) / Decimal('100')
            )
            
            obs = f"CST {cst} - Tributado"
            if cst in ['20', '70']:
                obs += f" com redução de {reducao_bc}%"
            
            return ResultadoImposto(
                base_calculo=CalculadoraImpostos.arredondar(base_calculo),
                aliquota=aliquota,
                valor=valor_icms,
                observacoes=obs
            )
        
        # CST não reconhecido
        return ResultadoImposto(
            base_calculo=Decimal('0'),
            aliquota=Decimal('0'),
            valor=Decimal('0'),
            observacoes=f"CST {cst} não reconhecido"
        )
    
    @staticmethod
    def calcular_icms_st(
        valor_produto: Decimal,
        aliquota_interna: Decimal,
        aliquota_interestadual: Decimal,
        mva: Decimal,  # Margem de Valor Agregado
        valor_frete: Optional[Decimal] = None,
        valor_seguro: Optional[Decimal] = None,
        outras_despesas: Optional[Decimal] = None,
        reducao_bc: Optional[Decimal] = None
    ) -> ResultadoImposto:
        """
        Calcula ICMS-ST (Substituição Tributária)
        
        Fórmula:
        BC ST = (Valor Produto + IPI + Frete + Seguro + Outras Despesas) * (1 + MVA/100)
        ICMS ST = (BC ST * Alíquota Interna) - ICMS Próprio
        """
        valor_produto = CalculadoraImpostos.to_decimal(valor_produto)
        valor_frete = CalculadoraImpostos.to_decimal(valor_frete)
        valor_seguro = CalculadoraImpostos.to_decimal(valor_seguro)
        outras_despesas = CalculadoraImpostos.to_decimal(outras_despesas)
        aliquota_interna = CalculadoraImpostos.to_decimal(aliquota_interna)
        aliquota_interestadual = CalculadoraImpostos.to_decimal(aliquota_interestadual)
        mva = CalculadoraImpostos.to_decimal(mva)
        reducao_bc = CalculadoraImpostos.to_decimal(reducao_bc or 0)
        
        # Base de cálculo original
        bc_original = valor_produto + valor_frete + valor_seguro + outras_despesas
        
        # Aplica redução se houver
        if reducao_bc > 0:
            bc_original = bc_original * (Decimal('100') - reducao_bc) / Decimal('100')
        
        # Base de cálculo ST com MVA
        bc_st = bc_original * (Decimal('1') + mva / Decimal('100'))
        
        # ICMS próprio (interestadual)
        icms_proprio = (bc_original * aliquota_interestadual) / Decimal('100')
        
        # ICMS ST
        icms_st_total = (bc_st * aliquota_interna) / Decimal('100')
        icms_st = icms_st_total - icms_proprio
        
        return ResultadoImposto(
            base_calculo=CalculadoraImpostos.arredondar(bc_st),
            aliquota=aliquota_interna,
            valor=CalculadoraImpostos.arredondar(icms_st),
            observacoes=f"ICMS-ST com MVA de {mva}%"
        )
    
    # ============================================
    # CÁLCULO DE IPI
    # ============================================
    
    @staticmethod
    def calcular_ipi(
        valor_produto: Decimal,
        cst: str,
        aliquota: Optional[Decimal] = None,
        valor_frete: Optional[Decimal] = None,
        valor_seguro: Optional[Decimal] = None,
        outras_despesas: Optional[Decimal] = None,
        valor_desconto: Optional[Decimal] = None
    ) -> ResultadoImposto:
        """
        Calcula IPI (Imposto sobre Produtos Industrializados)
        
        CST IPI:
        Entrada:
        - 00: Entrada com recuperação de crédito
        - 01: Entrada tributada com alíquota zero
        - 02: Entrada isenta
        - 03: Entrada não-tributada
        - 04: Entrada imune
        - 05: Entrada com suspensão
        
        Saída:
        - 50: Saída tributada
        - 51: Saída tributada com alíquota zero
        - 52: Saída isenta
        - 53: Saída não-tributada
        - 54: Saída imune
        - 55: Saída com suspensão
        """
        valor_produto = CalculadoraImpostos.to_decimal(valor_produto)
        valor_frete = CalculadoraImpostos.to_decimal(valor_frete)
        valor_seguro = CalculadoraImpostos.to_decimal(valor_seguro)
        outras_despesas = CalculadoraImpostos.to_decimal(outras_despesas)
        valor_desconto = CalculadoraImpostos.to_decimal(valor_desconto)
        
        # Base de cálculo IPI
        base_calculo = (
            valor_produto + valor_frete + valor_seguro + 
            outras_despesas - valor_desconto
        )
        
        # CSTs que não tributam IPI
        if cst in ['01', '02', '03', '04', '05', '51', '52', '53', '54', '55']:
            return ResultadoImposto(
                base_calculo=Decimal('0'),
                aliquota=Decimal('0'),
                valor=Decimal('0'),
                observacoes=f"CST {cst} - Sem IPI"
            )
        
        # CSTs que tributam IPI
        if cst in ['00', '49', '50', '99']:
            if aliquota is None:
                aliquota = Decimal('0')
            else:
                aliquota = CalculadoraImpostos.to_decimal(aliquota)
            
            valor_ipi = CalculadoraImpostos.arredondar(
                (base_calculo * aliquota) / Decimal('100')
            )
            
            return ResultadoImposto(
                base_calculo=CalculadoraImpostos.arredondar(base_calculo),
                aliquota=aliquota,
                valor=valor_ipi,
                observacoes=f"CST {cst} - Tributado"
            )
        
        return ResultadoImposto(
            base_calculo=Decimal('0'),
            aliquota=Decimal('0'),
            valor=Decimal('0'),
            observacoes=f"CST {cst} não reconhecido"
        )
    
    # ============================================
    # CÁLCULO DE PIS
    # ============================================
    
    @staticmethod
    def calcular_pis(
        valor_produto: Decimal,
        cst: str,
        regime: str = 'CUMULATIVO',
        aliquota_customizada: Optional[Decimal] = None,
        valor_frete: Optional[Decimal] = None,
        valor_seguro: Optional[Decimal] = None,
        outras_despesas: Optional[Decimal] = None,
        valor_desconto: Optional[Decimal] = None
    ) -> ResultadoImposto:
        """
        Calcula PIS (Programa de Integração Social)
        
        CST PIS:
        - 01: Operação Tributável com Alíquota Básica
        - 02: Operação Tributável com Alíquota Diferenciada
        - 03: Operação Tributável com Alíquota por Unidade de Medida
        - 04: Operação Tributável Monofásica - Revenda a Alíquota Zero
        - 05: Operação Tributável por Substituição Tributária
        - 06: Operação Tributável a Alíquota Zero
        - 07: Operação Isenta da Contribuição
        - 08: Operação sem Incidência da Contribuição
        - 09: Operação com Suspensão da Contribuição
        - 49: Outras Operações de Saída
        - 50-56: Operações com Direito a Crédito
        - 60-66: Crédito Presumido
        - 67: Crédito Presumido - Operação de Aquisição Vinculada
        - 70-75: Operação de Aquisição sem Direito a Crédito
        - 98: Outras Operações de Entrada
        - 99: Outras Operações
        
        Regime:
        - CUMULATIVO: 0,65%
        - NAO_CUMULATIVO: 1,65%
        """
        valor_produto = CalculadoraImpostos.to_decimal(valor_produto)
        valor_frete = CalculadoraImpostos.to_decimal(valor_frete)
        valor_seguro = CalculadoraImpostos.to_decimal(valor_seguro)
        outras_despesas = CalculadoraImpostos.to_decimal(outras_despesas)
        valor_desconto = CalculadoraImpostos.to_decimal(valor_desconto)
        
        # Base de cálculo PIS
        base_calculo = (
            valor_produto + valor_frete + valor_seguro + 
            outras_despesas - valor_desconto
        )
        
        # CSTs que não tributam PIS
        if cst in ['04', '05', '06', '07', '08', '09']:
            return ResultadoImposto(
                base_calculo=Decimal('0'),
                aliquota=Decimal('0'),
                valor=Decimal('0'),
                observacoes=f"CST {cst} - Sem PIS"
            )
        
        # CSTs que tributam PIS
        if cst in ['01', '02', '03', '49', '50', '51', '52', '53', '54', '55', '56', 
                   '60', '61', '62', '63', '64', '65', '66', '67', '70', '71', '72', 
                   '73', '74', '75', '98', '99']:
            
            # Define alíquota
            if aliquota_customizada is not None:
                aliquota = CalculadoraImpostos.to_decimal(aliquota_customizada)
            elif regime.upper() == 'CUMULATIVO':
                aliquota = CalculadoraImpostos.ALIQUOTA_PIS_REGIME_CUMULATIVO
            else:
                aliquota = CalculadoraImpostos.ALIQUOTA_PIS_REGIME_NAO_CUMULATIVO
            
            valor_pis = CalculadoraImpostos.arredondar(
                (base_calculo * aliquota) / Decimal('100')
            )
            
            return ResultadoImposto(
                base_calculo=CalculadoraImpostos.arredondar(base_calculo),
                aliquota=aliquota,
                valor=valor_pis,
                observacoes=f"CST {cst} - Regime {regime}"
            )
        
        return ResultadoImposto(
            base_calculo=Decimal('0'),
            aliquota=Decimal('0'),
            valor=Decimal('0'),
            observacoes=f"CST {cst} não reconhecido"
        )
    
    # ============================================
    # CÁLCULO DE COFINS
    # ============================================
    
    @staticmethod
    def calcular_cofins(
        valor_produto: Decimal,
        cst: str,
        regime: str = 'CUMULATIVO',
        aliquota_customizada: Optional[Decimal] = None,
        valor_frete: Optional[Decimal] = None,
        valor_seguro: Optional[Decimal] = None,
        outras_despesas: Optional[Decimal] = None,
        valor_desconto: Optional[Decimal] = None
    ) -> ResultadoImposto:
        """
        Calcula COFINS (Contribuição para Financiamento da Seguridade Social)
        
        CST COFINS: Mesmos códigos do PIS
        
        Regime:
        - CUMULATIVO: 3,00%
        - NAO_CUMULATIVO: 7,60%
        """
        valor_produto = CalculadoraImpostos.to_decimal(valor_produto)
        valor_frete = CalculadoraImpostos.to_decimal(valor_frete)
        valor_seguro = CalculadoraImpostos.to_decimal(valor_seguro)
        outras_despesas = CalculadoraImpostos.to_decimal(outras_despesas)
        valor_desconto = CalculadoraImpostos.to_decimal(valor_desconto)
        
        # Base de cálculo COFINS
        base_calculo = (
            valor_produto + valor_frete + valor_seguro + 
            outras_despesas - valor_desconto
        )
        
        # CSTs que não tributam COFINS
        if cst in ['04', '05', '06', '07', '08', '09']:
            return ResultadoImposto(
                base_calculo=Decimal('0'),
                aliquota=Decimal('0'),
                valor=Decimal('0'),
                observacoes=f"CST {cst} - Sem COFINS"
            )
        
        # CSTs que tributam COFINS
        if cst in ['01', '02', '03', '49', '50', '51', '52', '53', '54', '55', '56',
                   '60', '61', '62', '63', '64', '65', '66', '67', '70', '71', '72',
                   '73', '74', '75', '98', '99']:
            
            # Define alíquota
            if aliquota_customizada is not None:
                aliquota = CalculadoraImpostos.to_decimal(aliquota_customizada)
            elif regime.upper() == 'CUMULATIVO':
                aliquota = CalculadoraImpostos.ALIQUOTA_COFINS_REGIME_CUMULATIVO
            else:
                aliquota = CalculadoraImpostos.ALIQUOTA_COFINS_REGIME_NAO_CUMULATIVO
            
            valor_cofins = CalculadoraImpostos.arredondar(
                (base_calculo * aliquota) / Decimal('100')
            )
            
            return ResultadoImposto(
                base_calculo=CalculadoraImpostos.arredondar(base_calculo),
                aliquota=aliquota,
                valor=valor_cofins,
                observacoes=f"CST {cst} - Regime {regime}"
            )
        
        return ResultadoImposto(
            base_calculo=Decimal('0'),
            aliquota=Decimal('0'),
            valor=Decimal('0'),
            observacoes=f"CST {cst} não reconhecido"
        )
    
    # ============================================
    # CÁLCULO COMPLETO DE PRODUTO
    # ============================================
    
    @staticmethod
    def calcular_impostos_produto(
        valor_produto: Decimal,
        quantidade: Decimal,
        regime_tributario: str,  # 'SIMPLES_NACIONAL' ou 'NORMAL'
        cst_icms: str,
        cst_ipi: Optional[str] = None,
        cst_pis: Optional[str] = None,
        cst_cofins: Optional[str] = None,
        aliquota_icms: Optional[Decimal] = None,
        aliquota_ipi: Optional[Decimal] = None,
        aliquota_pis: Optional[Decimal] = None,
        aliquota_cofins: Optional[Decimal] = None,
        reducao_bc_icms: Optional[Decimal] = None,
        valor_desconto: Optional[Decimal] = None,
        valor_frete: Optional[Decimal] = None,
        valor_seguro: Optional[Decimal] = None,
        outras_despesas: Optional[Decimal] = None,
        aliquota_credito_sn: Optional[Decimal] = None,
        regime_pis_cofins: str = 'CUMULATIVO'
    ) -> Dict[str, Any]:
        """
        Calcula todos os impostos de um produto
        
        Retorna um dicionário completo com todos os cálculos
        """
        calc = CalculadoraImpostos()
        
        valor_produto = calc.to_decimal(valor_produto)
        quantidade = calc.to_decimal(quantidade)
        
        # Valor total do produto
        valor_total_produto = valor_produto * quantidade
        
        # ICMS
        if regime_tributario.upper() == 'SIMPLES_NACIONAL':
            icms = calc.calcular_icms_simples_nacional(
                valor_total_produto,
                cst_icms,
                aliquota_credito_sn
            )
        else:
            icms = calc.calcular_icms_regime_normal(
                valor_total_produto,
                cst_icms,
                aliquota_icms,
                reducao_bc_icms,
                valor_frete,
                valor_seguro,
                outras_despesas,
                valor_desconto
            )
        
        # IPI
        if cst_ipi:
            ipi = calc.calcular_ipi(
                valor_total_produto,
                cst_ipi,
                aliquota_ipi,
                valor_frete,
                valor_seguro,
                outras_despesas,
                valor_desconto
            )
        else:
            ipi = ResultadoImposto(Decimal('0'), Decimal('0'), Decimal('0'), "Não aplicável")
        
        # PIS
        if cst_pis:
            pis = calc.calcular_pis(
                valor_total_produto,
                cst_pis,
                regime_pis_cofins,
                aliquota_pis,
                valor_frete,
                valor_seguro,
                outras_despesas,
                valor_desconto
            )
        else:
            pis = ResultadoImposto(Decimal('0'), Decimal('0'), Decimal('0'), "Não aplicável")
        
        # COFINS
        if cst_cofins:
            cofins = calc.calcular_cofins(
                valor_total_produto,
                cst_cofins,
                regime_pis_cofins,
                aliquota_cofins,
                valor_frete,
                valor_seguro,
                outras_despesas,
                valor_desconto
            )
        else:
            cofins = ResultadoImposto(Decimal('0'), Decimal('0'), Decimal('0'), "Não aplicável")
        
        # Total de tributos
        total_tributos = icms.valor + ipi.valor + pis.valor + cofins.valor
        
        return {
            'valor_produto': float(valor_total_produto),
            'icms': {
                'base_calculo': float(icms.base_calculo),
                'aliquota': float(icms.aliquota),
                'valor': float(icms.valor),
                'observacoes': icms.observacoes
            },
            'ipi': {
                'base_calculo': float(ipi.base_calculo),
                'aliquota': float(ipi.aliquota),
                'valor': float(ipi.valor),
                'observacoes': ipi.observacoes
            },
            'pis': {
                'base_calculo': float(pis.base_calculo),
                'aliquota': float(pis.aliquota),
                'valor': float(pis.valor),
                'observacoes': pis.observacoes
            },
            'cofins': {
                'base_calculo': float(cofins.base_calculo),
                'aliquota': float(cofins.aliquota),
                'valor': float(cofins.valor),
                'observacoes': cofins.observacoes
            },
            'total_tributos': float(total_tributos)
        }
    
    # ============================================
    # CÁLCULO DE TOTAIS DA NOTA
    # ============================================
    
    @staticmethod
    def calcular_totais_nota(produtos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula os totais da nota fiscal com base na lista de produtos
        
        Cada produto deve ter os impostos já calculados
        """
        totais = {
            'base_calculo_icms': Decimal('0'),
            'valor_icms': Decimal('0'),
            'base_calculo_icms_st': Decimal('0'),
            'valor_icms_st': Decimal('0'),
            'valor_ipi': Decimal('0'),
            'valor_pis': Decimal('0'),
            'valor_cofins': Decimal('0'),
            'valor_produtos': Decimal('0'),
            'valor_frete': Decimal('0'),
            'valor_seguro': Decimal('0'),
            'valor_desconto': Decimal('0'),
            'outras_despesas': Decimal('0'),
            'valor_total_tributos': Decimal('0'),
            'valor_total_nota': Decimal('0')
        }
        
        for produto in produtos:
            # Soma valores dos produtos
            totais['valor_produtos'] += CalculadoraImpostos.to_decimal(
                produto.get('valor_total', 0)
            )
            
            # Soma ICMS
            if 'icms' in produto:
                totais['base_calculo_icms'] += CalculadoraImpostos.to_decimal(
                    produto['icms'].get('base_calculo', 0)
                )
                totais['valor_icms'] += CalculadoraImpostos.to_decimal(
                    produto['icms'].get('valor', 0)
                )
            
            # Soma IPI
            if 'ipi' in produto:
                totais['valor_ipi'] += CalculadoraImpostos.to_decimal(
                    produto['ipi'].get('valor', 0)
                )
            
            # Soma PIS
            if 'pis' in produto:
                totais['valor_pis'] += CalculadoraImpostos.to_decimal(
                    produto['pis'].get('valor', 0)
                )
            
            # Soma COFINS
            if 'cofins' in produto:
                totais['valor_cofins'] += CalculadoraImpostos.to_decimal(
                    produto['cofins'].get('valor', 0)
                )
            
            # Soma outros valores
            totais['valor_frete'] += CalculadoraImpostos.to_decimal(
                produto.get('valor_frete', 0)
            )
            totais['valor_seguro'] += CalculadoraImpostos.to_decimal(
                produto.get('valor_seguro', 0)
            )
            totais['valor_desconto'] += CalculadoraImpostos.to_decimal(
                produto.get('valor_desconto', 0)
            )
            totais['outras_despesas'] += CalculadoraImpostos.to_decimal(
                produto.get('outras_despesas', 0)
            )
        
        # Calcula total de tributos
        totais['valor_total_tributos'] = (
            totais['valor_icms'] +
            totais['valor_icms_st'] +
            totais['valor_ipi'] +
            totais['valor_pis'] +
            totais['valor_cofins']
        )
        
        # Calcula valor total da nota
        totais['valor_total_nota'] = (
            totais['valor_produtos'] +
            totais['valor_frete'] +
            totais['valor_seguro'] +
            totais['outras_despesas'] +
            totais['valor_ipi'] -
            totais['valor_desconto']
        )
        
        # Arredonda todos os valores
        for key in totais:
            totais[key] = float(CalculadoraImpostos.arredondar(totais[key]))
        
        return totais
