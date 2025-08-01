from datetime import datetime
import enum
from flask_login import UserMixin
from sqlalchemy import (
    Column, Integer, Numeric, String, Float, DateTime, Enum, ForeignKey, Text, DECIMAL,
    UniqueConstraint, Boolean, Table
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
    transferencia = "transferencia"

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
    pix_edfrance = "pix_edfrance"
    dinheiro = "dinheiro"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    a_prazo = "a_prazo"

class UnidadeMedida(str, enum.Enum):
    kg = "kg"
    saco = "saco"
    unidade = "unidade"
    fardo = "fardo"
    pacote = "pacote"

class TipoDesconto(str, enum.Enum):
    fixo = "fixo"
    percentual = "percentual"

class TipoEstoque(str, enum.Enum):
    loja = "loja"
    deposito = "deposito"
    fabrica = "fabrica"

class StatusPagamento(str, enum.Enum):
    pendente = "pendente"
    parcial = "parcial"
    quitado = "quitado"

# --------------------
# Tabela de associação para relacionamento muitos-para-muitos entre Produtos e Descontos
# --------------------
produto_desconto_association = Table(
    'produto_desconto_association',
    Base.metadata,
    Column('produto_id', Integer, ForeignKey('produtos.id'), primary_key=True),
    Column('desconto_id', Integer, ForeignKey('descontos.id'), primary_key=True),
    Column('sincronizado', Boolean, default=False, nullable=False)
)

# --------------------
# Entrega/Delivery
# --------------------
class Entrega(Base):
    __tablename__ = "entregas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    logradouro = Column(String(200), nullable=True)  
    numero = Column(String(20), nullable=True)       
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)      
    cidade = Column(String(100), nullable=True)      
    estado = Column(String(2), nullable=True)        
    cep = Column(String(10), nullable=True)          
    instrucoes = Column(Text, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
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
    sincronizado = Column(Boolean, default=False, nullable=False)

    movimentacoes = relationship("MovimentacaoEstoque", back_populates="usuario")
    notas_fiscais = relationship("NotaFiscal", back_populates="operador")
    caixas = relationship("Caixa", back_populates="operador")
    transferencias = relationship("TransferenciaEstoque", back_populates="usuario")

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
    sincronizado = Column(Boolean, default=False, nullable=False)

    operador = relationship("Usuario", back_populates="caixas")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="caixa")
    financeiros = relationship("Financeiro", back_populates="caixa")
    notas_fiscais = relationship("NotaFiscal", back_populates="caixa")
    pagamentos = relationship("PagamentoContaReceber", back_populates="caixa")

# --------------------
# Desconto (modelo principal)
# --------------------
class Desconto(Base):
    __tablename__ = "descontos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identificador = Column(String(50), unique=True, nullable=False)
    descricao = Column(String(255), nullable=True)
    tipo = Column(Enum(TipoDesconto), nullable=False)
    valor = Column(DECIMAL(10, 2), nullable=False)  # Pode ser valor fixo ou percentual
    quantidade_minima = Column(DECIMAL(12, 3), nullable=False)
    quantidade_maxima = Column(DECIMAL(12, 3), nullable=True)
    valido_ate = Column(DateTime, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)

    produtos = relationship(
        "Produto",
        secondary=produto_desconto_association,
        back_populates="descontos"
    )

    def __repr__(self):
        return (
            f"<Desconto("
            f"id={self.id}, "
            f"identificador='{self.identificador}', "
            f"tipo='{self.tipo.value}', "
            f"valor={float(self.valor):.2f}, "
            f"quantidade_minima={float(self.quantidade_minima):.3f}, "
            f"quantidade_maxima={float(self.quantidade_maxima):.3f if self.quantidade_maxima else None}, "
            f"descricao='{self.descricao}', "
            f"valido_ate='{self.valido_ate}', "
            f"ativo={self.ativo}, "
            f"sincronizado={self.sincronizado}"
            f")>"
        )

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

    valor_unitario_compra = Column(DECIMAL(10, 2), nullable=True)
    valor_total_compra = Column(DECIMAL(12, 2), nullable=True)
    imcs = Column(DECIMAL(5, 2), nullable=True)

    peso_kg_por_saco = Column(Numeric(10, 3), default=50.0)
    pacotes_por_saco = Column(Integer, default=10)
    pacotes_por_fardo = Column(Integer, default=5)
    estoque_loja = Column(DECIMAL(12, 3), nullable=False, default=0.0)
    estoque_deposito = Column(DECIMAL(12, 3), nullable=False, default=0.0)
    estoque_fabrica = Column(DECIMAL(12, 3), nullable=False, default=0.0)
    estoque_minimo = Column(DECIMAL(12, 3), nullable=False, default=0.0)
    estoque_maximo = Column(DECIMAL(12, 3), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)

    movimentacoes = relationship("MovimentacaoEstoque", back_populates="produto")
    itens_nf = relationship("NotaFiscalItem", back_populates="produto")

    # Relacionamento para transferências onde este produto é a origem
    transferencias_origem = relationship(
        "TransferenciaEstoque",
        foreign_keys="[TransferenciaEstoque.produto_id]",
        back_populates="produto"
    )
    # Relacionamento para transferências onde este produto é o destino
    transferencias_destino = relationship(
        "TransferenciaEstoque",
        foreign_keys="[TransferenciaEstoque.produto_destino_id]",
        back_populates="produto_destino"
    )
    
    # Relacionamento muitos-para-muitos com Descontos
    descontos = relationship(
        "Desconto",
        secondary=produto_desconto_association,
        back_populates="produtos"
    )

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
    limite_credito = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)

    notas_fiscais = relationship("NotaFiscal", back_populates="cliente")
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="cliente")
    financeiros = relationship("Financeiro", back_populates="cliente")
    contas_receber = relationship("ContaReceber", back_populates="cliente")

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
    estoque_origem = Column(Enum(TipoEstoque), nullable=True)
    estoque_destino = Column(Enum(TipoEstoque), nullable=True)
    quantidade = Column(DECIMAL(12, 3), nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    valor_recebido = Column(DECIMAL(12, 2), nullable=True)
    troco = Column(DECIMAL(12, 2), nullable=True)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=True)
    observacao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)

    produto = relationship("Produto", back_populates="movimentacoes")
    usuario = relationship("Usuario", back_populates="movimentacoes")
    cliente = relationship("Cliente", back_populates="movimentacoes")
    caixa = relationship("Caixa", back_populates="movimentacoes")

# --------------------
# Transferência entre Estoques
# --------------------
class TransferenciaEstoque(Base):
    __tablename__ = "transferencias_estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)  
    produto_destino_id = Column(Integer, ForeignKey("produtos.id"), nullable=True) 
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    estoque_origem = Column(Enum(TipoEstoque), nullable=False)
    estoque_destino = Column(Enum(TipoEstoque), nullable=False)
    quantidade = Column(DECIMAL(12, 3), nullable=False)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)
    observacao = Column(Text, nullable=True)
    
    # Campos para conversão (opcionais)
    quantidade_destino = Column(Numeric(10, 3), nullable=True)
    unidade_origem = Column(String(20), nullable=True)
    unidade_destino = Column(String(20), nullable=True)
    peso_kg_por_saco = Column(Numeric(10, 3), nullable=True)
    pacotes_por_saco = Column(Integer, nullable=True)
    pacotes_por_fardo = Column(Integer, nullable=True)
    
    sincronizado = Column(Boolean, default=False, nullable=False)

    produto = relationship(
        "Produto",
        foreign_keys=[produto_id],
        back_populates="transferencias_origem"
    )
    produto_destino = relationship(
        "Produto",
        foreign_keys=[produto_destino_id],
        back_populates="transferencias_destino"
    )
    usuario = relationship("Usuario", back_populates="transferencias")

# --------------------
# Nota Fiscal
# --------------------
class NotaFiscal(Base):
    __tablename__ = "notas_fiscais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    operador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=False)
    entrega_id = Column(Integer, ForeignKey("entregas.id"), nullable=True)
    data_emissao = Column(DateTime, default=datetime.utcnow, nullable=False)
    valor_total = Column(DECIMAL(12, 2), nullable=False)
    valor_desconto = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    tipo_desconto = Column(Enum(TipoDesconto), nullable=True)
    status = Column(Enum(StatusNota), nullable=False, default=StatusNota.emitida)
    chave_acesso = Column(String(60), unique=True, nullable=True)
    observacao = Column(Text, nullable=True)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    valor_recebido = Column(DECIMAL(12, 2), nullable=True)
    troco = Column(DECIMAL(12, 2), nullable=True)
    a_prazo = Column(Boolean, default=False, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    cliente = relationship("Cliente", back_populates="notas_fiscais")
    operador = relationship("Usuario", back_populates="notas_fiscais")
    caixa = relationship("Caixa", back_populates="notas_fiscais")
    entrega = relationship("Entrega")
    itens = relationship("NotaFiscalItem", back_populates="nota", cascade="all, delete-orphan")
    financeiros = relationship("Financeiro", back_populates="nota_fiscal", cascade="all, delete-orphan")
    contas_receber = relationship("ContaReceber", back_populates="nota_fiscal", cascade="all, delete-orphan")

# --------------------
# Item da Nota Fiscal
# --------------------
class NotaFiscalItem(Base):
    __tablename__ = "nota_fiscal_itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    estoque_origem = Column(Enum(TipoEstoque), nullable=False, default=TipoEstoque.loja)
    quantidade = Column(DECIMAL(12, 3), nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    valor_total = Column(DECIMAL(12, 2), nullable=False)
    desconto_aplicado = Column(DECIMAL(10, 2), nullable=True, default=0.00)
    tipo_desconto = Column(Enum(TipoDesconto), nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    nota = relationship("NotaFiscal", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_nf")

# --------------------
# Contas a Receber
# --------------------
class ContaReceber(Base):
    __tablename__ = "contas_receber"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=True)
    descricao = Column(Text, nullable=False)
    valor_original = Column(DECIMAL(12, 2), nullable=False)
    valor_aberto = Column(DECIMAL(12, 2), nullable=False)
    data_vencimento = Column(DateTime, nullable=False)
    data_emissao = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(StatusPagamento), default=StatusPagamento.pendente, nullable=False)
    observacoes = Column(Text, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)

    cliente = relationship("Cliente", back_populates="contas_receber")
    nota_fiscal = relationship("NotaFiscal", back_populates="contas_receber")
    pagamentos = relationship("PagamentoContaReceber", back_populates="conta", cascade="all, delete-orphan")

    def registrar_pagamento(self, valor_pago, forma_pagamento, caixa_id=None, observacoes=None):
        if valor_pago <= 0:
            raise ValueError("Valor do pagamento deve ser positivo")
        if valor_pago > self.valor_aberto:
            raise ValueError("Valor do pagamento excede o valor em aberto")
        
        pagamento = PagamentoContaReceber(
            conta_id=self.id,
            caixa_id=caixa_id,
            valor_pago=valor_pago,
            forma_pagamento=forma_pagamento,
            observacoes=observacoes
        )
        db.session.add(pagamento)
        
        self.valor_aberto -= valor_pago
        self.status = StatusPagamento.quitado if self.valor_aberto == 0 else StatusPagamento.parcial
        
        financeiro = Financeiro(
            tipo=TipoMovimentacao.entrada,
            categoria=CategoriaFinanceira.venda,
            valor=valor_pago,
            conta_receber_id=self.id,
            cliente_id=self.cliente_id,
            caixa_id=caixa_id,
            descricao=f"Pagamento conta #{self.id}"
        )
        db.session.add(financeiro)
        
        return pagamento

# --------------------
# Pagamentos de Contas a Receber
# --------------------
class PagamentoContaReceber(Base):
    __tablename__ = "pagamentos_contas_receber"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conta_id = Column(Integer, ForeignKey("contas_receber.id"), nullable=False)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=True)
    valor_pago = Column(DECIMAL(12, 2), nullable=False)
    data_pagamento = Column(DateTime, default=datetime.utcnow, nullable=False)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    observacoes = Column(Text, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)

    conta = relationship("ContaReceber", back_populates="pagamentos")
    caixa = relationship("Caixa", back_populates="pagamentos")

# --------------------
# Financeiro
# --------------------
class Financeiro(Base):
    __tablename__ = "financeiro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    categoria = Column(Enum(CategoriaFinanceira), nullable=False)
    valor = Column(DECIMAL(12, 2), nullable=False)
    valor_desconto = Column(DECIMAL(12, 2), nullable=True, default=0.00)
    descricao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=True)
    nota_fiscal = relationship("NotaFiscal", back_populates="financeiros")

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente = relationship("Cliente", back_populates="financeiros")

    caixa_id = Column(Integer, ForeignKey('caixas.id'), nullable=True)
    caixa = relationship("Caixa", back_populates="financeiros")
    
    conta_receber_id = Column(Integer, ForeignKey("contas_receber.id"), nullable=True)
    conta_receber = relationship("ContaReceber")
    
    def to_raw_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo.value if self.tipo else None,
            'categoria': self.categoria.value if self.categoria else None,
            'valor': float(self.valor),
            'valor_desconto': float(self.valor_desconto) if self.valor_desconto else None,
            'descricao': self.descricao,
            'data': self.data.isoformat() if self.data else None,
            'nota_fiscal_id': self.nota_fiscal_id,
            'cliente_id': self.cliente_id,
            'caixa_id': self.caixa_id,
            'conta_receber_id': self.conta_receber_id
        }