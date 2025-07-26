from pydantic import BaseModel, constr, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import Annotated

Decimal12_3 = Annotated[Decimal, Field(max_digits=12, decimal_places=3)]
Decimal10_2 = Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
CPFType = Annotated[str, Field(min_length=11, max_length=14)]

class TipoUsuario(str, Enum):
    admin = "admin"
    operador = "operador"

class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"

class FormaPagamento(str, Enum):
    pix_fabiano = "pix_fabiano"
    pix_maquineta = "pix_maquineta"
    dinheiro = "dinheiro"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    a_prazo = "a_prazo"

class StatusNota(str, Enum):
    emitida = "emitida"
    cancelada = "cancelada"

class CategoriaFinanceira(str, Enum):
    venda = "venda"
    compra = "compra"
    despesa = "despesa"
    salario = "salario"
    outro = "outro"
    abertura_caixa = "abertura_caixa"
    fechamento_caixa = "fechamento_caixa"

class UnidadeMedida(str, Enum):
    kg = "kg"
    saco = "saco"
    unidade = "unidade"

# --------------------
# Usuário
# --------------------
class UsuarioBase(BaseModel):
    nome: str
    cpf: CPFType
    tipo: TipoUsuario
    observacoes: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    senha: str
    status: Optional[bool] = True

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[CPFType] = None
    tipo: Optional[TipoUsuario] = None
    senha: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[bool] = None

class UsuarioRead(UsuarioBase):
    id: int
    criado_em: datetime
    ativo: bool
    ultimo_acesso: Optional[datetime] = None

    class Config:
        orm_mode = True

# --------------------
# Produto
# --------------------
class ProdutoBase(BaseModel):
    codigo: Optional[str] = Field(None, max_length=50)
    nome: Optional[str] = Field(None, max_length=150)
    tipo: Optional[str] = Field(None, max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    unidade: Optional[UnidadeMedida] = None
    valor_unitario: Optional[Decimal10_2] = None
    estoque_quantidade: Optional[Decimal12_3] = None
    ativo: Optional[bool] = None

class ProdutoCreate(ProdutoBase):
    nome: str = Field(..., max_length=150)
    tipo: str = Field(..., max_length=50)
    unidade: UnidadeMedida = Field(...)
    valor_unitario: Decimal10_2 = Field(...)
    estoque_quantidade: Decimal12_3 = Field(default=Decimal('0.0'))

class ProdutoUpdate(ProdutoBase):
    pass

class ProdutoRead(ProdutoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        orm_mode = True

# --------------------
# Cliente
# --------------------
class ClienteBase(BaseModel):
    nome: str
    documento: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    endereco: Optional[str]
    ativo: Optional[bool] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteRead(ClienteBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        orm_mode = True

# --------------------
# Caixa
# --------------------
class StatusCaixa(str, Enum):
    aberto = "aberto"
    fechado = "fechado"

class CaixaBase(BaseModel):
    operador_id: int
    valor_abertura: Decimal10_2
    status: Optional[StatusCaixa] = StatusCaixa.aberto
    observacoes: Optional[str] = None
    data_abertura: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None
    valor_fechamento: Optional[Decimal10_2] = None

class CaixaCreate(CaixaBase):
    pass

class CaixaRead(CaixaBase):
    id: int

    class Config:
        orm_mode = True

# --------------------
# Movimentacao Estoque
# --------------------
class MovimentacaoEstoqueBase(BaseModel):
    produto_id: int
    usuario_id: int
    cliente_id: Optional[int] = None
    caixa_id: int
    tipo: TipoMovimentacao
    quantidade: Decimal12_3
    valor_unitario: Decimal10_2
    valor_recebido: Optional[Decimal10_2] = None
    troco: Optional[Decimal10_2] = None
    forma_pagamento: Optional[FormaPagamento] = None
    observacao: Optional[str] = None

class MovimentacaoEstoqueCreate(MovimentacaoEstoqueBase):
    pass

class MovimentacaoEstoqueRead(MovimentacaoEstoqueBase):
    id: int
    data: datetime

    class Config:
        orm_mode = True

# --------------------
# Nota Fiscal Item
# --------------------
class NotaFiscalItemBase(BaseModel):
    produto_id: int
    quantidade: Decimal12_3
    valor_unitario: Decimal10_2
    valor_total: Decimal10_2

class NotaFiscalItemCreate(NotaFiscalItemBase):
    pass

class NotaFiscalItemRead(NotaFiscalItemBase):
    id: int

    class Config:
        orm_mode = True

# --------------------
# Nota Fiscal
# --------------------
class NotaFiscalBase(BaseModel):
    cliente_id: Optional[int]
    operador_id: int
    caixa_id: int
    data_emissao: Optional[datetime] = None
    valor_total: Decimal10_2
    status: StatusNota = StatusNota.emitida
    chave_acesso: Optional[str] = None
    observacao: Optional[str] = None
    forma_pagamento: FormaPagamento
    valor_recebido: Optional[Decimal10_2] = None
    troco: Optional[Decimal10_2] = None

class NotaFiscalCreate(NotaFiscalBase):
    itens: List[NotaFiscalItemCreate]

class NotaFiscalRead(NotaFiscalBase):
    id: int
    itens: List[NotaFiscalItemRead]

    class Config:
        orm_mode = True

# --------------------
# Financeiro
# --------------------
class FinanceiroBase(BaseModel):
    tipo: TipoMovimentacao
    categoria: CategoriaFinanceira
    valor: Decimal10_2
    descricao: Optional[str] = None
    data: Optional[datetime] = None
    nota_fiscal_id: Optional[int] = None
    cliente_id: Optional[int] = None
    caixa_id: Optional[int] = None

class FinanceiroCreate(FinanceiroBase):
    pass

class FinanceiroRead(FinanceiroBase):
    id: int

    class Config:
        orm_mode = True
