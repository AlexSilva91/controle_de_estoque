"""
app/models/associations.py

Tabelas de associação para evitar importação circular entre modelos
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, Boolean, UniqueConstraint
)
from .base import Base

# --------------------
# Tabela de associação para relacionamento muitos-para-muitos entre ProdutosFiscais e Produtos
# --------------------
class ProdutoFiscalProduto(Base):
    """Tabela de associação entre ProdutoFiscal e Produto"""
    __tablename__ = "produto_fiscal_produto_association"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_fiscal_id = Column(Integer, ForeignKey("produtos_fiscais.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('produto_fiscal_id', 'produto_id', 
                        name='uq_produto_fiscal_produto'),
    )
    
    def __repr__(self):
        return f"<ProdutoFiscalProduto(produto_fiscal_id={self.produto_fiscal_id}, produto_id={self.produto_id})>"