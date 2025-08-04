from pydantic import BaseModel, constr, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import Annotated

Decimal12_2 = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]
Decimal12_3 = Annotated[Decimal, Field(max_digits=12, decimal_places=3)]
Decimal10_2 = Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
CPFType = Annotated[str, Field(min_length=11, max_length=14)]

class TipoUsuario(str, Enum):
    admin = "admin"
    operador = "operador"

class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"
    transferencia = "transferencia"

class StatusNota(str, Enum):
    emitida = "emitida"
    cancelada = "cancelada"

class StatusCaixa(str, Enum):
    aberto = "aberto"
    fechado = "fechado"

class CategoriaFinanceira(str, Enum):
    venda = "venda"
    compra = "compra"
    despesa = "despesa"
    salario = "salario"
    outro = "outro"
    abertura_caixa = "abertura_caixa"
    fechamento_caixa = "fechamento_caixa"

class FormaPagamento(str, Enum):
    pix_fabiano = "pix_fabiano"
    pix_edfrance = "pix_edfrance"
    pix_maquineta = "pix_maquineta"
    pix_loja = "pix_loja"
    dinheiro = "dinheiro"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    a_prazo = "a_prazo"

class UnidadeMedida(str, Enum):
    kg = "kg"
    saco = "saco"
    unidade = "unidade"
    fardo = "fardo"
    pacote = "pacote"

class TipoDesconto(str, Enum):
    fixo = "fixo"
    percentual = "percentual"

class TipoEstoque(str, Enum):
    loja = "loja"
    deposito = "deposito"
    fabrica = "fabrica"

class StatusPagamento(str, Enum):
    pendente = "pendente"
    parcial = "parcial"
    quitado = "quitado"

# --------------------
# Entrega/Delivery
# --------------------
class EntregaBase(BaseModel):
    logradouro: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    instrucoes: Optional[str] = None

class EntregaCreate(EntregaBase):
    pass

class EntregaRead(EntregaBase):
    id: int
    sincronizado: bool = False

    class Config:
        from_attributes = True

# --------------------
# Usuário
# --------------------
class UsuarioBase(BaseModel):
    nome: str = Field(..., max_length=100)
    cpf: CPFType
    tipo: TipoUsuario
    observacoes: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    senha: str
    status: bool = True

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    cpf: Optional[CPFType] = None
    tipo: Optional[TipoUsuario] = None
    senha: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[bool] = None
    ultimo_acesso: Optional[datetime] = None

class UsuarioRead(UsuarioBase):
    id: int
    criado_em: datetime
    status: bool
    ultimo_acesso: Optional[datetime] = None
    sincronizado: bool = False

    class Config:
        from_attributes = True

# --------------------
# Caixa
# --------------------
class CaixaBase(BaseModel):
    operador_id: int
    valor_abertura: Decimal12_2
    status: StatusCaixa = StatusCaixa.aberto
    observacoes: Optional[str] = None
    data_abertura: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None
    valor_fechamento: Optional[Decimal12_2] = None

class CaixaCreate(CaixaBase):
    pass

class CaixaRead(CaixaBase):
    id: int
    sincronizado: bool = False

    class Config:
        from_attributes = True

# --------------------
# Desconto
# --------------------
class DescontoBase(BaseModel):
    identificador: str = Field(..., max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    tipo: TipoDesconto
    valor: Decimal10_2
    quantidade_minima: Decimal12_3
    quantidade_maxima: Optional[Decimal12_3] = None
    valido_ate: Optional[datetime] = None
    ativo: bool = True

class DescontoCreate(DescontoBase):
    produtos_ids: Optional[List[int]] = None

class DescontoUpdate(BaseModel):
    identificador: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    tipo: Optional[TipoDesconto] = None
    valor: Optional[Decimal10_2] = None
    quantidade_minima: Optional[Decimal12_3] = None
    quantidade_maxima: Optional[Decimal12_3] = None
    valido_ate: Optional[datetime] = None
    ativo: Optional[bool] = None
    produtos_ids: Optional[List[int]] = None

class DescontoRead(DescontoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    sincronizado: bool = False
    produtos: List["ProdutoRead"] = []

    class Config:
        from_attributes = True

# --------------------
# Produto
# --------------------
class ProdutoBase(BaseModel):
    codigo: Optional[str] = Field(None, max_length=50)
    nome: str = Field(..., max_length=150)
    tipo: str = Field(..., max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    unidade: UnidadeMedida = UnidadeMedida.kg
    valor_unitario: Decimal10_2
    valor_unitario_compra: Optional[Decimal10_2] = None
    valor_total_compra: Optional[Decimal12_2] = None
    imcs: Optional[Decimal12_3] = None
    peso_kg_por_saco: Decimal = Decimal('50.0')
    pacotes_por_saco: int = 10
    pacotes_por_fardo: int = 5
    estoque_loja: Decimal12_3 = Decimal('0.0')
    estoque_deposito: Decimal12_3 = Decimal('0.0')
    estoque_fabrica: Decimal12_3 = Decimal('0.0')
    estoque_minimo: Decimal12_3 = Decimal('0.0')
    estoque_maximo: Optional[Decimal12_3] = None
    ativo: bool = True

class ProdutoCreate(ProdutoBase):
    descontos_ids: Optional[List[int]] = None

class ProdutoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=50)
    nome: Optional[str] = Field(None, max_length=150)
    tipo: Optional[str] = Field(None, max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    unidade: Optional[UnidadeMedida] = None
    valor_unitario: Optional[Decimal10_2] = None
    valor_unitario_compra: Optional[Decimal10_2] = None
    valor_total_compra: Optional[Decimal12_2] = None
    imcs: Optional[Decimal12_3] = None
    peso_kg_por_saco: Optional[Decimal] = None
    pacotes_por_saco: Optional[int] = None
    pacotes_por_fardo: Optional[int] = None
    estoque_loja: Optional[Decimal12_3] = None
    estoque_deposito: Optional[Decimal12_3] = None
    estoque_fabrica: Optional[Decimal12_3] = None
    estoque_minimo: Optional[Decimal12_3] = None
    estoque_maximo: Optional[Decimal12_3] = None
    ativo: Optional[bool] = None
    descontos_ids: Optional[List[int]] = None

class ProdutoRead(ProdutoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    sincronizado: bool = False
    descontos: List[DescontoRead] = []

    class Config:
        from_attributes = True

# --------------------
# Cliente
# --------------------
class ClienteBase(BaseModel):
    nome: str = Field(..., max_length=150)
    documento: Optional[str] = Field(None, max_length=20)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    endereco: Optional[str] = None
    limite_credito: Decimal12_2 = Decimal('0.00')
    ativo: bool = True

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=150)
    documento: Optional[str] = Field(None, max_length=20)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    endereco: Optional[str] = None
    limite_credito: Optional[Decimal12_2] = None
    ativo: Optional[bool] = None

class ClienteRead(ClienteBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    sincronizado: bool = False

    class Config:
        from_attributes = True

# --------------------
# Movimentação de Estoque
# --------------------
class MovimentacaoEstoqueBase(BaseModel):
    produto_id: int
    usuario_id: int
    cliente_id: Optional[int] = None
    caixa_id: int
    tipo: TipoMovimentacao
    estoque_origem: Optional[TipoEstoque] = None
    estoque_destino: Optional[TipoEstoque] = None
    quantidade: Decimal12_3
    valor_unitario: Decimal10_2
    valor_recebido: Optional[Decimal12_2] = None
    troco: Optional[Decimal12_2] = None
    forma_pagamento: Optional[FormaPagamento] = None
    observacao: Optional[str] = None

class MovimentacaoEstoqueCreate(MovimentacaoEstoqueBase):
    pass

class MovimentacaoEstoqueRead(MovimentacaoEstoqueBase):
    id: int
    data: datetime
    sincronizado: bool = False
    produto: Optional[ProdutoRead] = None
    usuario: Optional[UsuarioRead] = None
    cliente: Optional[ClienteRead] = None
    caixa: Optional[CaixaRead] = None

    class Config:
        from_attributes = True

# --------------------
# Transferência entre Estoques
# --------------------
class TransferenciaEstoqueBase(BaseModel):
    produto_id: int
    produto_destino_id: Optional[int] = None
    usuario_id: int
    estoque_origem: TipoEstoque
    estoque_destino: TipoEstoque
    quantidade: Decimal12_3
    observacao: Optional[str] = None
    quantidade_destino: Optional[Decimal12_3] = None
    unidade_origem: Optional[str] = Field(None, max_length=20)
    unidade_destino: Optional[str] = Field(None, max_length=20)
    peso_kg_por_saco: Optional[Decimal] = None
    pacotes_por_saco: Optional[int] = None
    pacotes_por_fardo: Optional[int] = None

class TransferenciaEstoqueCreate(TransferenciaEstoqueBase):
    pass

class TransferenciaEstoqueRead(TransferenciaEstoqueBase):
    id: int
    data: datetime
    sincronizado: bool = False
    produto: Optional[ProdutoRead] = None
    produto_destino: Optional[ProdutoRead] = None
    usuario: Optional[UsuarioRead] = None

    class Config:
        from_attributes = True

# --------------------
# Nota Fiscal Item
# --------------------
class NotaFiscalItemBase(BaseModel):
    produto_id: int
    estoque_origem: TipoEstoque = TipoEstoque.loja
    quantidade: Decimal12_3
    valor_unitario: Decimal10_2
    valor_total: Decimal12_2
    desconto_aplicado: Decimal10_2 = Decimal('0.00')
    tipo_desconto: Optional[TipoDesconto] = None

class NotaFiscalItemCreate(NotaFiscalItemBase):
    pass

class NotaFiscalItemRead(NotaFiscalItemBase):
    id: int
    sincronizado: bool = False
    produto: Optional[ProdutoRead] = None

    class Config:
        from_attributes = True

# --------------------
# Nota Fiscal
# --------------------
class NotaFiscalBase(BaseModel):
    cliente_id: Optional[int] = None
    operador_id: int
    caixa_id: int
    entrega_id: Optional[int] = None
    data_emissao: Optional[datetime] = None
    valor_total: Decimal12_2
    valor_desconto: Decimal12_2 = Decimal('0.00')
    tipo_desconto: Optional[TipoDesconto] = None
    status: StatusNota = StatusNota.emitida
    chave_acesso: Optional[str] = Field(None, max_length=60)
    observacao: Optional[str] = None
    forma_pagamento: FormaPagamento
    valor_recebido: Optional[Decimal12_2] = None
    troco: Optional[Decimal12_2] = None
    a_prazo: bool = False

class NotaFiscalCreate(NotaFiscalBase):
    itens: List[NotaFiscalItemCreate]

class NotaFiscalRead(NotaFiscalBase):
    id: int
    sincronizado: bool = False
    itens: List[NotaFiscalItemRead] = []
    cliente: Optional[ClienteRead] = None
    operador: Optional[UsuarioRead] = None
    caixa: Optional[CaixaRead] = None
    entrega: Optional[EntregaRead] = None

    class Config:
        from_attributes = True

# --------------------
# Contas a Receber
# --------------------
class ContaReceberBase(BaseModel):
    cliente_id: int
    nota_fiscal_id: Optional[int] = None
    descricao: str
    valor_original: Decimal12_2
    valor_aberto: Decimal12_2
    data_vencimento: datetime
    data_emissao: Optional[datetime] = None
    status: StatusPagamento = StatusPagamento.pendente
    observacoes: Optional[str] = None

class ContaReceberCreate(ContaReceberBase):
    pass

class ContaReceberRead(ContaReceberBase):
    id: int
    sincronizado: bool = False
    cliente: Optional[ClienteRead] = None
    nota_fiscal: Optional[NotaFiscalRead] = None
    pagamentos: List["PagamentoContaReceberRead"] = []

    class Config:
        from_attributes = True

# --------------------
# Pagamentos de Contas a Receber
# --------------------
class PagamentoContaReceberBase(BaseModel):
    conta_id: int
    caixa_id: Optional[int] = None
    valor_pago: Decimal12_2
    forma_pagamento: FormaPagamento
    observacoes: Optional[str] = None

class PagamentoContaReceberCreate(PagamentoContaReceberBase):
    pass

class PagamentoContaReceberRead(PagamentoContaReceberBase):
    id: int
    data_pagamento: datetime
    sincronizado: bool = False
    conta: Optional[ContaReceberRead] = None
    caixa: Optional[CaixaRead] = None

    class Config:
        from_attributes = True

# --------------------
# Financeiro
# --------------------
class FinanceiroBase(BaseModel):
    tipo: TipoMovimentacao
    categoria: CategoriaFinanceira
    valor: Decimal12_2
    valor_desconto: Decimal12_2 = Decimal('0.00')
    descricao: Optional[str] = None
    data: Optional[datetime] = None
    nota_fiscal_id: Optional[int] = None
    cliente_id: Optional[int] = None
    caixa_id: Optional[int] = None
    conta_receber_id: Optional[int] = None

class FinanceiroCreate(FinanceiroBase):
    pass

class FinanceiroUpdate(BaseModel):
    tipo: Optional[TipoMovimentacao] = None
    categoria: Optional[CategoriaFinanceira] = None
    valor: Optional[Decimal12_2] = None
    valor_desconto: Optional[Decimal12_2] = None
    descricao: Optional[str] = None
    nota_fiscal_id: Optional[int] = None
    cliente_id: Optional[int] = None
    caixa_id: Optional[int] = None
    conta_receber_id: Optional[int] = None

class FinanceiroRead(FinanceiroBase):
    id: int
    data: datetime
    sincronizado: bool = False
    nota_fiscal: Optional[NotaFiscalRead] = None
    cliente: Optional[ClienteRead] = None
    caixa: Optional[CaixaRead] = None
    conta_receber: Optional[ContaReceberRead] = None

    class Config:
        from_attributes = True

# Resolver referências circulares
ProdutoRead.update_forward_refs()
DescontoRead.update_forward_refs()
ContaReceberRead.update_forward_refs()
PagamentoContaReceberRead.update_forward_refs()
NotaFiscalRead.update_forward_refs()
NotaFiscalItemRead.update_forward_refs()
MovimentacaoEstoqueRead.update_forward_refs()
TransferenciaEstoqueRead.update_forward_refs()
FinanceiroRead.update_forward_refs()