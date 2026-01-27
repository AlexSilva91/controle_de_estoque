from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .base import Base

# Importe todos os modelos do arquivo entities.py
from .entities import (
    # Enums
    TipoUsuario,
    TipoMovimentacao,
    StatusNota,
    StatusCaixa,
    CategoriaFinanceira,
    FormaPagamento,
    UnidadeMedida,
    TipoDesconto,
    TipoEstoque,
    StatusPagamento,
    
    # Tabela de associação
    produto_desconto_association,
    
    # Modelos principais
    Conta,
    SaldoFormaPagamento,
    MovimentacaoConta,
    Entrega,
    Usuario,
    Caixa,
    Desconto,
    PagamentoNotaFiscal,
    LoteEstoque,
    Produto,
    Cliente,
    MovimentacaoEstoque,
    TransferenciaEstoque,
    
    # Modelos de XML da NFe
    NFeXML,
    NFeIdeXML,
    NFeEmitenteXML,
    NFeDestinatarioXML,
    NFeDetalheXML,
    NFeImpostoItemXML,
    NFeImpostoXML,
    NFeTransporteXML,
    NFePagamentoXML,
    NFeDuplicataXML,
    NFeProtocoloXML,
    
    # Modelos de notas fiscais e financeiro
    NotaFiscal,
    NotaFiscalItem,
    ContaReceber,
    PagamentoContaReceber,
    Financeiro,
    
    # Modelos de auditoria e configuração
    AuditLog,
    Configuracao,
)

# Importe os novos modelos fiscais do arquivo fiscal_models.py
from .fiscal_models import (
    ConfiguracaoFiscal,
    ProdutoFiscal,
    Transportadora,
    VeiculoTransporte,
    NotaFiscalHistorico,
    NotaFiscalEvento,
    NotaFiscalVolume,
)

# Lista de todos os modelos disponíveis para importação
__all__ = [
    # Base
    'Base',
    
    # Enums
    'TipoUsuario',
    'TipoMovimentacao',
    'StatusNota',
    'StatusCaixa',
    'CategoriaFinanceira',
    'FormaPagamento',
    'UnidadeMedida',
    'TipoDesconto',
    'TipoEstoque',
    'StatusPagamento',
    
    # Tabela de associação
    'produto_desconto_association',
    
    # Modelos principais (entities.py)
    'Conta',
    'SaldoFormaPagamento',
    'MovimentacaoConta',
    'Entrega',
    'Usuario',
    'Caixa',
    'Desconto',
    'PagamentoNotaFiscal',
    'LoteEstoque',
    'Produto',
    'Cliente',
    'MovimentacaoEstoque',
    'TransferenciaEstoque',
    
    # Modelos XML NFe
    'NFeXML',
    'NFeIdeXML',
    'NFeEmitenteXML',
    'NFeDestinatarioXML',
    'NFeDetalheXML',
    'NFeImpostoItemXML',
    'NFeImpostoXML',
    'NFeTransporteXML',
    'NFePagamentoXML',
    'NFeDuplicataXML',
    'NFeProtocoloXML',
    
    # Notas Fiscais e Financeiro
    'NotaFiscal',
    'NotaFiscalItem',
    'ContaReceber',
    'PagamentoContaReceber',
    'Financeiro',
    
    # Auditoria e Configuração
    'AuditLog',
    'Configuracao',
    
    # Novos modelos fiscais (fiscal_models.py)
    'ConfiguracaoFiscal',
    'ProdutoFiscal',
    'Transportadora',
    'VeiculoTransporte',
    'NotaFiscalHistorico',
    'NotaFiscalEvento',
    'NotaFiscalVolume',
]

# Conveniência: você também pode criar grupos lógicos
MODELOS_PRINCIPAIS = [
    'Usuario', 'Produto', 'Cliente', 'NotaFiscal', 'Caixa', 'Conta'
]

MODELOS_FISCAIS = [
    'ConfiguracaoFiscal',
    'ProdutoFiscal',
    'Transportadora',
    'VeiculoTransporte',
    'NotaFiscalHistorico',
    'NotaFiscalEvento',
    'NotaFiscalVolume',
]

MODELOS_XML = [
    'NFeXML',
    'NFeIdeXML',
    'NFeEmitenteXML',
    'NFeDestinatarioXML',
    'NFeDetalheXML',
    'NFeImpostoItemXML',
    'NFeImpostoXML',
    'NFeTransporteXML',
    'NFePagamentoXML',
    'NFeDuplicataXML',
    'NFeProtocoloXML',
]