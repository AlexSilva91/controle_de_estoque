from pydantic import BaseModel, computed_field, constr, condecimal, Field
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

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[CPFType] = None
    tipo: Optional[TipoUsuario] = None
    senha: Optional[str] = None

class UsuarioRead(UsuarioBase):
    id: int
    criado_em: datetime

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
    valor_unitario: Optional[float] = None
    estoque_quantidade: Optional[float] = None
    ativo: Optional[bool] = None

class ProdutoCreate(ProdutoBase):
    nome: str = Field(..., max_length=150)
    tipo: str = Field(..., max_length=50)
    unidade: UnidadeMedida = Field(...)
    valor_unitario: float = Field(...)
    estoque_quantidade: float = Field(0.0)

class ProdutoUpdate(ProdutoBase):
    pass

class Produto(ProdutoBase):
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
# Movimentação Estoque
# --------------------
class MovimentacaoEstoqueBase(BaseModel):
    produto_id: int
    usuario_id: int
    cliente_id: Optional[int] = None
    tipo: TipoMovimentacao
    quantidade: Decimal12_3
    valor_unitario: Decimal10_2
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
    data_emissao: Optional[datetime]
    status: StatusNota
    chave_acesso: Optional[str]
    observacao: Optional[str]
    
    @computed_field
    @property
    def valor_total(self) -> Decimal10_2:
        return Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario))


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
    descricao: Optional[str]
    data: Optional[datetime] = None
    nota_fiscal_id: Optional[int] = None

class FinanceiroCreate(FinanceiroBase):
    pass

class FinanceiroRead(FinanceiroBase):
    id: int

    class Config:
        orm_mode = True
