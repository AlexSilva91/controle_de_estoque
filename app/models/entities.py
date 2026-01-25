from datetime import datetime
import enum
from flask_login import UserMixin
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    DECIMAL,
    UniqueConstraint,
    Boolean,
    Table,
    func,
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
    saida_estorno = "saida_estorno"
    transferencia = "transferencia"


class StatusNota(str, enum.Enum):
    emitida = "emitida"
    cancelada = "cancelada"


class StatusCaixa(str, enum.Enum):
    aberto = "aberto"
    fechado = "fechado"
    em_analise = "em_analise"
    recusado = "recusado"
    aprovado = "aprovado"


class CategoriaFinanceira(str, enum.Enum):
    venda = "venda"
    compra = "compra"
    despesa = "despesa"
    estorno = "estorno"
    salario = "salario"
    outro = "outro"
    abertura_caixa = "abertura_caixa"
    fechamento_caixa = "fechamento_caixa"


class FormaPagamento(str, enum.Enum):
    pix_fabiano = "pix_fabiano"
    pix_maquineta = "pix_maquineta"
    pix_edfrance = "pix_edfrance"
    pix_loja = "pix_loja"
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
    "produto_desconto_association",
    Base.metadata,
    Column("produto_id", Integer, ForeignKey("produtos.id"), primary_key=True),
    Column("desconto_id", Integer, ForeignKey("descontos.id"), primary_key=True),
    Column("sincronizado", Boolean, default=False, nullable=False),
)


# --------------------
# Conta do Usuário
# --------------------
class Conta(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, unique=True)
    saldo_total = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    status = Column(Boolean, default=True, nullable=False)
    atualizado_em = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    sincronizado = Column(Boolean, default=False, nullable=False)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="conta")
    saldos_forma_pagamento = relationship(
        "SaldoFormaPagamento", back_populates="conta", cascade="all, delete-orphan"
    )
    movimentacoes = relationship("MovimentacaoConta", back_populates="conta")

    @property
    def saldo_geral(self):
        """Retorna o saldo total"""
        return float(self.saldo_total) if self.saldo_total else 0.00

    def get_saldo_forma_pagamento(self, forma_pagamento):
        """Retorna saldo específico por forma de pagamento"""
        saldo = next(
            (
                s
                for s in self.saldos_forma_pagamento
                if s.forma_pagamento == forma_pagamento
            ),
            None,
        )
        return float(saldo.saldo) if saldo else 0.00

    def get_usuario_nome(self):
        """Retorna o nome do usuário associado à conta"""
        return self.usuario.nome if self.usuario else None

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "saldo_total": float(self.saldo_total),
            "saldos_por_forma_pagamento": {
                saldo.forma_pagamento.value: float(saldo.saldo)
                for saldo in self.saldos_forma_pagamento
            },
            "atualizado_em": (
                self.atualizado_em.isoformat() if self.atualizado_em else None
            ),
        }


# --------------------
# Saldo por Forma de Pagamento
# --------------------
class SaldoFormaPagamento(Base):
    __tablename__ = "saldos_forma_pagamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    saldo = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    atualizado_em = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    sincronizado = Column(Boolean, default=False, nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "conta_id", "forma_pagamento", name="uq_conta_forma_pagamento"
        ),
    )

    # Relacionamentos
    conta = relationship("Conta", back_populates="saldos_forma_pagamento")


# --------------------
# Movimentação de Conta
# --------------------
class MovimentacaoConta(Base):
    __tablename__ = "movimentacoes_contas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    valor = Column(DECIMAL(12, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.now, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=True)

    # Relacionamentos
    conta = relationship("Conta", back_populates="movimentacoes")
    usuario = relationship("Usuario")
    caixa = relationship("Caixa")


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
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    ultimo_acesso = Column(DateTime, nullable=True)
    observacoes = Column(Text, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)

    # Relacionamento 1:1 com Conta
    conta = relationship("Conta", back_populates="usuario", uselist=False)

    # Relacionamentos existentes...
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="usuario")
    notas_fiscais = relationship("NotaFiscal", back_populates="operador")
    caixas_operados = relationship(
        "Caixa", foreign_keys="[Caixa.operador_id]", back_populates="operador"
    )
    caixas_analisados = relationship(
        "Caixa", foreign_keys="[Caixa.administrador_id]", back_populates="administrador"
    )
    transferencias = relationship("TransferenciaEstoque", back_populates="usuario")


# --------------------
# Caixa (Modelo modificado com controle de fechamento)
# --------------------
class Caixa(Base):
    __tablename__ = "caixas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    administrador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    data_abertura = Column(DateTime, default=datetime.now, nullable=False)
    data_fechamento = Column(DateTime, nullable=True)
    data_analise = Column(DateTime, nullable=True)
    valor_abertura = Column(DECIMAL(12, 2), nullable=False)
    valor_fechamento = Column(DECIMAL(12, 2), nullable=True)
    valor_confirmado = Column(DECIMAL(12, 2), nullable=True)
    status = Column(Enum(StatusCaixa), nullable=False, default=StatusCaixa.aberto)
    observacoes_operador = Column(Text, nullable=True)
    observacoes_admin = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)

    operador = relationship(
        "Usuario", foreign_keys=[operador_id], back_populates="caixas_operados"
    )
    administrador = relationship(
        "Usuario", foreign_keys=[administrador_id], back_populates="caixas_analisados"
    )
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="caixa")
    financeiros = relationship("Financeiro", back_populates="caixa")
    notas_fiscais = relationship("NotaFiscal", back_populates="caixa")
    pagamentos = relationship("PagamentoContaReceber", back_populates="caixa")

    def fechar_caixa(
        self, valor_fechamento, observacoes_operador=None, usuario_id=None
    ):
        """Método para fechar o caixa (aguardando aprovação)"""

        self.valor_fechamento = valor_fechamento
        self.data_fechamento = datetime.now()
        self.observacoes_operador = observacoes_operador
        self.status = StatusCaixa.em_analise
        self.sincronizado = False

        # Cria registro financeiro do fechamento (pendente)
        fechamento = Financeiro(
            tipo=TipoMovimentacao.saida,
            categoria=CategoriaFinanceira.fechamento_caixa,
            valor=valor_fechamento,
            descricao=f"Fechamento do caixa #{self.id} (pendente)",
            caixa_id=self.id,
            data=self.data_fechamento,
        )
        db.session.add(fechamento)

    def aprovar_fechamento(
        self, administrador_id, valor_confirmado=None, observacoes_admin=None
    ):
        """Método para aprovar o fechamento do caixa"""

        self.valor_confirmado = (
            valor_confirmado if valor_confirmado else self.valor_fechamento
        )
        self.observacoes_admin = observacoes_admin
        self.administrador_id = administrador_id
        self.data_analise = datetime.now()
        self.status = StatusCaixa.aprovado
        self.sincronizado = False

        # Atualiza registro financeiro do fechamento
        fechamento = Financeiro.query.filter_by(
            caixa_id=self.id, categoria=CategoriaFinanceira.fechamento_caixa
        ).first()

        if fechamento:
            fechamento.valor = self.valor_confirmado
            fechamento.descricao = f"Fechamento do caixa #{self.id}"
            fechamento.data = self.data_analise

    def rejeitar_fechamento(self, administrador_id, motivo, valor_correto=None):
        """Método para rejeitar o fechamento do caixa"""

        self.valor_confirmado = valor_correto
        self.observacoes_admin = motivo
        self.administrador_id = administrador_id
        self.data_analise = datetime.now()
        self.status = StatusCaixa.recusado
        self.sincronizado = False

        # Remove registro financeiro do fechamento
        fechamento = Financeiro.query.filter_by(
            caixa_id=self.id, categoria=CategoriaFinanceira.fechamento_caixa
        ).first()

        if fechamento:
            db.session.delete(fechamento)

    def reabrir_caixa(self, administrador_id, motivo=None):
        """Método para reabrir um caixa fechado ou recusado"""
        if self.status not in [StatusCaixa.fechado, StatusCaixa.recusado]:
            raise ValueError("Caixa não está fechado ou recusado")

        self.status = StatusCaixa.aberto
        self.data_fechamento = None
        self.data_analise = None
        self.administrador_id = administrador_id
        self.observacoes_admin = (
            f"Reabertura: {motivo}" if motivo else "Reabertura do caixa"
        )
        self.sincronizado = False

        # Remove registro financeiro do fechamento se existir
        fechamento = Financeiro.query.filter_by(
            caixa_id=self.id, categoria=CategoriaFinanceira.fechamento_caixa
        ).first()

        if fechamento:
            db.session.delete(fechamento)

    def to_dict(self, incluir_relacionamentos=True):
        """Retorna todas as informações do caixa em formato de dicionário"""
        data = {
            "id": self.id,
            "operador_id": self.operador_id,
            "operador": self.operador.nome if self.operador else None,
            "administrador_id": self.administrador_id,
            "administrador": self.administrador.nome if self.administrador else None,
            "data_abertura": (
                self.data_abertura.isoformat() if self.data_abertura else None
            ),
            "data_fechamento": (
                self.data_fechamento.isoformat() if self.data_fechamento else None
            ),
            "data_analise": (
                self.data_analise.isoformat() if self.data_analise else None
            ),
            "valor_abertura": (
                float(self.valor_abertura) if self.valor_abertura else None
            ),
            "valor_fechamento": (
                float(self.valor_fechamento) if self.valor_fechamento else None
            ),
            "valor_confirmado": (
                float(self.valor_confirmado) if self.valor_confirmado else None
            ),
            "status": self.status.value if self.status else None,
            "observacoes_operador": self.observacoes_operador,
            "observacoes_admin": self.observacoes_admin,
            "observacoes": self.observacoes,
            "sincronizado": self.sincronizado,
        }

        if incluir_relacionamentos:
            data["movimentacoes"] = [
                {
                    "id": m.id,
                    "produto_id": m.produto_id,
                    "produto": m.produto.nome if m.produto else None,
                    "usuario_id": m.usuario_id,
                    "usuario": m.usuario.nome if m.usuario else None,
                    "cliente_id": m.cliente_id,
                    "cliente": m.cliente.nome if m.cliente else None,
                    "tipo": m.tipo.value if m.tipo else None,
                    "quantidade": float(m.quantidade),
                    "valor_unitario": float(m.valor_unitario),
                    "valor_recebido": (
                        float(m.valor_recebido) if m.valor_recebido else None
                    ),
                    "forma_pagamento": (
                        m.forma_pagamento.value if m.forma_pagamento else None
                    ),
                    "data": m.data.isoformat() if m.data else None,
                }
                for m in self.movimentacoes
            ]

            data["notas_fiscais"] = [
                {
                    "id": nf.id,
                    "cliente_id": nf.cliente_id,
                    "cliente": nf.cliente.nome if nf.cliente else None,
                    "operador_id": nf.operador_id,
                    "operador": nf.operador.nome if nf.operador else None,
                    "valor_total": float(nf.valor_total),
                    "valor_desconto": float(nf.valor_desconto),
                    "status": nf.status.value if nf.status else None,
                    "forma_pagamento": (
                        nf.forma_pagamento.value if nf.forma_pagamento else None
                    ),
                    "data_emissao": (
                        nf.data_emissao.isoformat() if nf.data_emissao else None
                    ),
                }
                for nf in self.notas_fiscais
            ]

            data["pagamentos"] = [
                {
                    "id": p.id,
                    "conta_id": p.conta_id,
                    "valor_pago": float(p.valor_pago),
                    "forma_pagamento": (
                        p.forma_pagamento.value if p.forma_pagamento else None
                    ),
                    "data_pagamento": (
                        p.data_pagamento.isoformat() if p.data_pagamento else None
                    ),
                }
                for p in self.pagamentos
            ]

            data["financeiros"] = [f.to_raw_dict() for f in self.financeiros]

        return data


# --------------------
# Desconto (modelo principal)
# --------------------
class Desconto(Base):
    __tablename__ = "descontos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identificador = Column(String(50), unique=True, nullable=False)
    descricao = Column(String(255), nullable=True)
    tipo = Column(Enum(TipoDesconto), nullable=False)
    valor = Column(DECIMAL(10, 2), nullable=False)
    quantidade_minima = Column(DECIMAL(12, 3), nullable=False)
    quantidade_maxima = Column(DECIMAL(12, 3), nullable=True)
    valido_ate = Column(DateTime, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    sincronizado = Column(Boolean, default=False, nullable=False)

    produtos = relationship(
        "Produto", secondary=produto_desconto_association, back_populates="descontos"
    )

    def __repr__(self):
        qtd_maxima = (
            f"{float(self.quantidade_maxima):.3f}"
            if self.quantidade_maxima is not None
            else "None"
        )
        return (
            f"<Desconto("
            f"id={self.id}, "
            f"identificador='{self.identificador}', "
            f"tipo='{self.tipo.value}', "
            f"valor={float(self.valor):.2f}, "
            f"quantidade_minima={float(self.quantidade_minima):.3f}, "
            f"quantidade_maxima={qtd_maxima}, "
            f"descricao='{self.descricao}', "
            f"valido_ate='{self.valido_ate}', "
            f"ativo={self.ativo}, "
            f"sincronizado={self.sincronizado}"
            f")>"
        )


# --------------------
# Pagamentos de Nota Fiscal (para múltiplos pagamentos)
# --------------------
class PagamentoNotaFiscal(Base):
    __tablename__ = "pagamentos_nota_fiscal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    valor = Column(DECIMAL(12, 2), nullable=False)
    data = Column(
        DateTime, default=datetime.now(ZoneInfo("America/Sao_Paulo")), nullable=False
    )
    sincronizado = Column(Boolean, default=False, nullable=False)

    nota_fiscal = relationship("NotaFiscal", back_populates="pagamentos")


# --------------------
# Lote de Estoque
# --------------------
class LoteEstoque(Base):
    __tablename__ = "lotes_estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade_inicial = Column(DECIMAL(12, 3), nullable=False)
    quantidade_disponivel = Column(DECIMAL(12, 3), nullable=False)
    valor_unitario_compra = Column(DECIMAL(12, 2), nullable=False)
    data_entrada = Column(DateTime, default=datetime.now, nullable=False)
    observacao = Column(Text, nullable=True)
    ativo = Column(Boolean, default=False, nullable=False)

    produto = relationship("Produto", back_populates="lotes")


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
    foto = Column(String(255), nullable=True)

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
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    sincronizado = Column(Boolean, default=False, nullable=False)

    movimentacoes = relationship("MovimentacaoEstoque", back_populates="produto")
    itens_nf = relationship("NotaFiscalItem", back_populates="produto")
    lotes = relationship(
        "LoteEstoque", back_populates="produto", cascade="all, delete-orphan"
    )

    transferencias_origem = relationship(
        "TransferenciaEstoque",
        foreign_keys="[TransferenciaEstoque.produto_id]",
        back_populates="produto",
    )
    transferencias_destino = relationship(
        "TransferenciaEstoque",
        foreign_keys="[TransferenciaEstoque.produto_destino_id]",
        back_populates="produto_destino",
    )

    descontos = relationship(
        "Desconto", secondary=produto_desconto_association, back_populates="produtos"
    )

    @classmethod
    def gerar_codigo_sequencial(cls):
        """
        Gera um código sequencial único para produtos, preenchendo lacunas.
        Exemplo: se existem códigos 1,2,4,5 -> gera 3
        """
        # Busca todos os códigos existentes que sejam numéricos
        produtos = cls.query.filter(cls.codigo.isnot(None)).all()

        numeros_existentes = set()
        for p in produtos:
            if p.codigo:
                try:
                    numero = int(p.codigo)
                    numeros_existentes.add(numero)
                except ValueError:
                    continue  # ignora códigos não numéricos existentes

        # Começa do 1 e procura o menor número disponível
        novo_numero = 1
        while novo_numero in numeros_existentes:
            novo_numero += 1

        return str(novo_numero)

    @classmethod
    def get_estoque(cls, tipo_estoque):
        """Retorna o estoque específico baseado no tipo"""
        if tipo_estoque == TipoEstoque.loja:
            return cls.estoque_loja
        elif tipo_estoque == TipoEstoque.deposito:
            return cls.estoque_deposito
        elif tipo_estoque == TipoEstoque.fabrica:
            return cls.estoque_fabrica
        else:
            return cls.estoque_loja


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
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
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
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=True)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    estoque_origem = Column(Enum(TipoEstoque), nullable=True)
    estoque_destino = Column(Enum(TipoEstoque), nullable=True)
    quantidade = Column(DECIMAL(12, 3), nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    valor_unitario_compra = Column(DECIMAL(10, 2), nullable=True)
    valor_recebido = Column(DECIMAL(12, 2), nullable=True)
    troco = Column(DECIMAL(12, 2), nullable=True)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=True)
    observacao = Column(Text, nullable=True)
    data = Column(DateTime, default=datetime.now, nullable=False)
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
    data = Column(DateTime, default=datetime.now, nullable=False)
    observacao = Column(Text, nullable=True)

    quantidade_destino = Column(Numeric(10, 3), nullable=True)
    unidade_origem = Column(String(20), nullable=True)
    unidade_destino = Column(String(20), nullable=True)
    peso_kg_por_saco = Column(Numeric(10, 3), nullable=True)
    pacotes_por_saco = Column(Integer, nullable=True)
    pacotes_por_fardo = Column(Integer, nullable=True)

    sincronizado = Column(Boolean, default=False, nullable=False)

    produto = relationship(
        "Produto", foreign_keys=[produto_id], back_populates="transferencias_origem"
    )
    produto_destino = relationship(
        "Produto",
        foreign_keys=[produto_destino_id],
        back_populates="transferencias_destino",
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
    data_emissao = Column(DateTime, default=datetime.now, nullable=False)
    valor_total = Column(DECIMAL(12, 2), nullable=False)
    valor_desconto = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    tipo_desconto = Column(Enum(TipoDesconto), nullable=True)
    status = Column(Enum(StatusNota), nullable=False, default=StatusNota.emitida)
    chave_acesso = Column(String(60), unique=True, nullable=True)
    observacao = Column(Text, nullable=True)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=True)
    valor_recebido = Column(DECIMAL(12, 2), nullable=True)
    troco = Column(DECIMAL(12, 2), nullable=True)
    a_prazo = Column(Boolean, default=False, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)

    cliente = relationship("Cliente", back_populates="notas_fiscais")
    operador = relationship("Usuario", back_populates="notas_fiscais")
    caixa = relationship("Caixa", back_populates="notas_fiscais")
    entrega = relationship("Entrega")
    itens = relationship(
        "NotaFiscalItem", back_populates="nota", cascade="all, delete-orphan"
    )
    financeiros = relationship(
        "Financeiro", back_populates="nota_fiscal", cascade="all, delete-orphan"
    )
    contas_receber = relationship(
        "ContaReceber", back_populates="nota_fiscal", cascade="all, delete-orphan"
    )
    pagamentos = relationship(
        "PagamentoNotaFiscal",
        back_populates="nota_fiscal",
        cascade="all, delete-orphan",
    )

    @classmethod
    def obter_vendas_do_dia(cls, data=None, caixa_id=None, operador_id=None):
        """
        Obtém todas as vendas do dia especificado ou do dia atual se nenhuma data for fornecida
        Retorna apenas vendas associadas a caixas com status 'aberto'

        Args:
            data (date, optional): Data para filtrar as vendas. Defaults to None (hoje).
            caixa_id (int, optional): ID do caixa para filtrar. Defaults to None.
            operador_id (int, optional): ID do operador para filtrar. Defaults to None.

        Returns:
            List[NotaFiscal]: Lista de notas fiscais do dia
        """
        # Define a data como hoje se não for especificada
        if data is None:
            data = datetime.now(ZoneInfo("America/Sao_Paulo")).date()

        # Converte para datetime para comparar com o campo DateTime do banco
        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = datetime.combine(data, datetime.max.time())

        # Cria la query base
        query = cls.query.join(Caixa, cls.caixa_id == Caixa.id).filter(
            cls.data_emissao >= inicio_dia,
            cls.data_emissao <= fim_dia,
            cls.status == StatusNota.emitida,
            Caixa.status == StatusCaixa.aberto,  # Filtra apenas caixas abertos
        )

        # Aplica filtros adicionais se fornecidos
        if caixa_id:
            query = query.filter(cls.caixa_id == caixa_id)

        if operador_id:
            query = query.filter(cls.operador_id == operador_id)

        return query.order_by(cls.data_emissao.desc()).all()


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
    data_emissao = Column(DateTime, default=datetime.now, nullable=False)
    data_pagamento = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(
        Enum(StatusPagamento), default=StatusPagamento.pendente, nullable=False
    )
    observacoes = Column(Text, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)

    cliente = relationship("Cliente", back_populates="contas_receber")
    nota_fiscal = relationship("NotaFiscal", back_populates="contas_receber")
    pagamentos = relationship(
        "PagamentoContaReceber", back_populates="conta", cascade="all, delete-orphan"
    )

    def registrar_pagamento(
        self,
        valor_pago,
        forma_pagamento,
        caixa_id=None,
        observacoes=None,
        data_pagamento=None,
    ):
        if valor_pago <= 0:
            raise ValueError("Valor do pagamento deve ser positivo")
        if valor_pago > self.valor_aberto:
            raise ValueError("Valor do pagamento excede o valor em aberto")

        # SEMPRE usa a data e hora atuais, ignorando qualquer parâmetro recebido
        data_pagamento = datetime.now()

        # Atualiza as observações da conta se fornecidas
        if observacoes is not None and observacoes.strip() != "":
            if self.observacoes:
                self.observacoes += (
                    f"\n{data_pagamento.strftime('%d/%m/%Y %H:%M')}: {observacoes}"
                )
            else:
                self.observacoes = (
                    f"{data_pagamento.strftime('%d/%m/%Y %H:%M')}: {observacoes}"
                )

        pagamento = PagamentoContaReceber(
            conta_id=self.id,
            caixa_id=caixa_id,
            valor_pago=valor_pago,
            forma_pagamento=forma_pagamento,
            observacoes=observacoes,
            data_pagamento=data_pagamento,
        )
        db.session.add(pagamento)

        self.valor_aberto -= valor_pago
        self.data_pagamento = data_pagamento
        self.status = (
            StatusPagamento.quitado
            if self.valor_aberto == 0
            else StatusPagamento.parcial
        )

        financeiro = Financeiro(
            tipo=TipoMovimentacao.entrada,
            categoria=CategoriaFinanceira.venda,
            valor=valor_pago,
            conta_receber_id=self.id,
            cliente_id=self.cliente_id,
            caixa_id=caixa_id,
            descricao=f"Pagamento conta #{self.id} - {observacoes if observacoes else ''}".strip(),
            data=data_pagamento,
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
    data_pagamento = Column(DateTime, default=datetime.now, nullable=False)
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
    data = Column(DateTime, default=datetime.now, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)

    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=True)
    nota_fiscal = relationship("NotaFiscal", back_populates="financeiros")

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente = relationship("Cliente", back_populates="financeiros")

    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=True)
    caixa = relationship("Caixa", back_populates="financeiros")

    pagamento_id = Column(
        Integer, ForeignKey("pagamentos_nota_fiscal.id"), nullable=True
    )
    pagamento = relationship("PagamentoNotaFiscal")
    conta_receber_id = Column(Integer, ForeignKey("contas_receber.id"), nullable=True)
    conta_receber = relationship("ContaReceber")

    def to_raw_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo.value if self.tipo else None,
            "categoria": self.categoria.value if self.categoria else None,
            "valor": float(self.valor),
            "valor_desconto": (
                float(self.valor_desconto) if self.valor_desconto else None
            ),
            "descricao": self.descricao,
            "data": self.data.isoformat() if self.data else None,
            "nota_fiscal_id": self.nota_fiscal_id,
            "cliente_id": self.cliente_id,
            "caixa_id": self.caixa_id,
            "conta_receber_id": self.conta_receber_id,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tabela = Column(String(100), nullable=False)
    registro_id = Column(Integer, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    acao = Column(String(50), nullable=False)  # insert, update, delete
    antes = Column(Text, nullable=True)  # JSON com estado anterior
    depois = Column(Text, nullable=True)  # JSON com estado posterior
    criado_em = Column(DateTime, default=datetime.now, nullable=False)

    usuario = relationship("Usuario")


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    permitir_venda_sem_estoque = Column(Boolean, default=False, nullable=False)
    atualizado_em = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    @classmethod
    def get_config(cls, session):
        config = session.query(cls).first()
        if not config:
            config = cls()
            session.add(config)
            session.commit()
        return config
