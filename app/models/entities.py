from datetime import datetime
import enum
from flask_login import UserMixin
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, DECIMAL,
    UniqueConstraint, Boolean
)
from sqlalchemy.orm import relationship
from . import db
from .base import Base
from datetime import datetime
from zoneinfo import ZoneInfo

# --------------------
# Enums
# --------------------
class TipoUsuario(str, enum.Enum):
    admin = "admin"
    operador = "operador"

class TipoMovimentacao(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"

class StatusNota(str, enum.Enum):
    emitida = "emitida"
    cancelada = "cancelada"

class StatusCaixa(str, enum.Enum):
    aberto = "aberto"
    fechado = "fechado"

class CategoriaFinanceira(str, enum.Enum):
    venda = "venda"
    compra = "compra"
    despesa = "despesa"
    salario = "salario"
    outro = "outro"
    abertura_caixa = "abertura_caixa"
    fechamento_caixa = "fechamento_caixa"

class FormaPagamento(str, enum.Enum):
    pix_fabiano = "pix_fabiano"
    pix_maquineta = "pix_maquineta"
    dinheiro = "dinheiro"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    a_prazo = "a_prazo"

class UnidadeMedida(str, enum.Enum):
    kg = "kg"
    saco = "saco"
    unidade = "unidade"

# --------------------
# Usuário
# --------------------
class Usuario(UserMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("cpf", name="uq_usuario_cpf"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(14), nullable=False, unique=True)
    senha_hash = Column(Text, nullable=False)
    tipo = Column(Enum(TipoUsuario), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    ultimo_acesso = Column(DateTime, nullable=True)
    observacoes = Column(Text, nullable=True)

    movimentacoes = relationship("MovimentacaoEstoque", back_populates="usuario")
    notas_fiscais = relationship("NotaFiscal", back_populates="operador")
    caixas = relationship("Caixa", back_populates="operador")

# --------------------
# Caixa
# --------------------
class Caixa(Base):
    __tablename__ = "caixas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_abertura = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_fechamento = Column(DateTime, nullable=True)
    valor_abertura = Column(DECIMAL(12, 2), nullable=False)
    valor_fechamento = Column(DECIMAL(12, 2), nullable=True)
    status = Column(Enum(StatusCaixa), nullable=False, default=StatusCaixa.aberto)
    observacoes = Column(Text, nullable=True)

    operador = relationship("Usuario", back_populates="caixas")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="caixa")
    financeiros = relationship("Financeiro", back_populates="caixa")

# --------------------
# Produto
# --------------------
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=True)
    nome = Column(String(150), nullable=False)
    tipo = Column(String(50), nullable=False)
    marca = Column(String(100), nullable=True)
    unidade = Column(Enum(UnidadeMedida), nullable=False, default=UnidadeMedida.kg)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    estoque_quantidade = Column(DECIMAL(12, 3), nullable=False, default=0.0)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    movimentacoes = relationship("MovimentacaoEstoque", back_populates="produto")
    itens_nf = relationship("NotaFiscalItem", back_populates="produto")

# --------------------
# Cliente
# --------------------
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    documento = Column(String(20), nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    endereco = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    notas_fiscais = relationship("NotaFiscal", back_populates="cliente")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="cliente")
    financeiros = relationship("Financeiro", back_populates="cliente")

# --------------------
# Movimentação de Estoque
# --------------------
class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(DECIMAL(12, 3), nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    valor_recebido = Column(DECIMAL(12, 2), nullable=True)  # Novo campo
    troco = Column(DECIMAL(12, 2), nullable=True)  # Novo campo
    forma_pagamento = Column(Enum(FormaPagamento), nullable=True)
    observacao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)

    produto = relationship("Produto", back_populates="movimentacoes")
    usuario = relationship("Usuario", back_populates="movimentacoes")
    cliente = relationship("Cliente", back_populates="movimentacoes")
    caixa = relationship("Caixa", back_populates="movimentacoes")

# --------------------
# Nota Fiscal
# --------------------
class NotaFiscal(Base):
    __tablename__ = "notas_fiscais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    operador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=False)
    data_emissao = Column(DateTime, default=datetime.utcnow, nullable=False)
    valor_total = Column(DECIMAL(12, 2), nullable=False)
    status = Column(Enum(StatusNota), nullable=False, default=StatusNota.emitida)
    chave_acesso = Column(String(60), unique=True, nullable=True)
    observacao = Column(Text, nullable=True)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    valor_recebido = Column(DECIMAL(12, 2), nullable=True)  # Novo campo
    troco = Column(DECIMAL(12, 2), nullable=True)  # Novo campo

    cliente = relationship("Cliente", back_populates="notas_fiscais")
    operador = relationship("Usuario", back_populates="notas_fiscais")
    caixa = relationship("Caixa")
    itens = relationship("NotaFiscalItem", back_populates="nota", cascade="all, delete-orphan")
    financeiros = relationship("Financeiro", back_populates="nota_fiscal", cascade="all, delete-orphan")

# --------------------
# Item da Nota Fiscal
# --------------------
class NotaFiscalItem(Base):
    __tablename__ = "nota_fiscal_itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(DECIMAL(12, 3), nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    valor_total = Column(DECIMAL(12, 2), nullable=False)

    nota = relationship("NotaFiscal", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_nf")

# --------------------
# Financeiro
# --------------------
class Financeiro(Base):
    __tablename__ = "financeiro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    categoria = Column(Enum(CategoriaFinanceira), nullable=False)
    valor = Column(DECIMAL(12, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)

    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=True)
    nota_fiscal = relationship("NotaFiscal", back_populates="financeiros")

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente = relationship("Cliente", back_populates="financeiros")

    caixa_id = db.Column(db.Integer, db.ForeignKey('caixas.id'), nullable=True)
    caixa = relationship("Caixa", back_populates="financeiros")