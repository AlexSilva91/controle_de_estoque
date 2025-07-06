from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import schemas
from app.models import entities
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

class TipoUsuario(str, Enum):
    admin = "admin"
    operador = "operador"

class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"

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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== Utilitários =====
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def validar_cpf(cpf: str) -> bool:
    """Valida o formato do CPF (apenas dígitos, 11 caracteres)."""
    cpf = ''.join(filter(str.isdigit, cpf))
    return len(cpf) == 11

def validar_documento(documento: str) -> bool:
    """Valida formato básico de documento (CPF ou CNPJ)."""
    doc = ''.join(filter(str.isdigit, documento))
    return len(doc) in (11, 14)  # CPF tem 11, CNPJ tem 14

# ===== Usuários =====
def get_user_by_cpf(db: Session, cpf: str):
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido. Deve conter 11 dígitos.")
    
    clean_cpf = cpf.replace('.', '').replace('-', '')
    return (
        db.query(entities.Usuario)
        .filter(
            func.replace(func.replace(entities.Usuario.cpf, '.', ''), '-', '') == clean_cpf
        )
        .first()
    )

def get_user_by_id(db: Session, user_id: int):
    return db.query(entities.Usuario).filter(entities.Usuario.id == user_id).first()

def get_usuarios(db: Session):
    return db.query(entities.Usuario).all()

def create_user(db: Session, user: schemas.UsuarioCreate):
    # Validações
    if not validar_cpf(user.cpf):
        raise ValueError("CPF inválido. Deve conter 11 dígitos.")
    
    if get_user_by_cpf(db, user.cpf):
        raise ValueError("CPF já cadastrado.")
    
    if user.tipo not in [t.value for t in TipoUsuario]:
        raise ValueError(f"Tipo de usuário inválido. Deve ser um dos: {[t.value for t in TipoUsuario]}")
    
    if len(user.senha) < 6:
        raise ValueError("Senha deve ter pelo menos 6 caracteres.")
    
    hashed_password = pwd_context.hash(user.senha)
    db_user = entities.Usuario(
        nome=user.nome,
        cpf=user.cpf,
        senha_hash=hashed_password,
        tipo=user.tipo,
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar usuário no banco de dados.")

# ===== Produto =====
def get_produto(db: Session, produto_id: int):
    return db.query(entities.Produto).filter(entities.Produto.id == produto_id, entities.Produto.ativo == True).first()

def get_produtos(db: Session):
    return db.query(entities.Produto).filter(entities.Produto.ativo == True).all()

def create_produto(db: Session, produto: schemas.ProdutoCreate):
    # Validações
    if produto.codigo:
        existing = db.query(entities.Produto).filter(entities.Produto.codigo == produto.codigo).first()
        if existing:
            raise ValueError("Código de produto já cadastrado.")
    
    if produto.unidade not in [u.value for u in UnidadeMedida]:
        raise ValueError(f"Unidade de medida inválida. Deve ser um dos: {[u.value for u in UnidadeMedida]}")
    
    if produto.valor_unitario <= 0:
        raise ValueError("Valor unitário deve ser maior que zero.")
    
    if produto.estoque_quantidade < 0:
        raise ValueError("Quantidade em estoque não pode ser negativa.")
    
    db_produto = entities.Produto(**produto.dict())
    db.add(db_produto)
    try:
        db.commit()
        db.refresh(db_produto)
        return db_produto
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar produto no banco de dados.")

def update_produto(db: Session, produto_id: int, produto_data: schemas.ProdutoUpdate):
    produto = db.query(entities.Produto).filter(entities.Produto.id == produto_id, entities.Produto.ativo == True).first()
    if not produto:
        raise ValueError("Produto não encontrado ou inativo.")
    
    # Validações apenas para campos que estão sendo atualizados
    update_data = produto_data.dict(exclude_unset=True)
    
    if "unidade" in update_data and update_data["unidade"] not in [u.value for u in UnidadeMedida]:
        raise ValueError(f"Unidade de medida inválida. Deve ser um dos: {[u.value for u in UnidadeMedida]}")
    
    if "valor_unitario" in update_data and update_data["valor_unitario"] <= 0:
        raise ValueError("Valor unitário deve ser maior que zero.")
    
    if "estoque_quantidade" in update_data and update_data["estoque_quantidade"] < 0:
        raise ValueError("Quantidade em estoque não pode ser negativa.")
    
    for field, value in update_data.items():
        setattr(produto, field, value)
    
    produto.atualizado_em = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(produto)
        return produto
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao atualizar produto no banco de dados.")

def delete_produto(db: Session, produto_id: int):
    produto = db.query(entities.Produto).filter(entities.Produto.id == produto_id, entities.Produto.ativo == True).first()
    if not produto:
        raise ValueError("Produto não encontrado ou já inativo.")
    
    produto.ativo = False
    produto.atualizado_em = datetime.utcnow()
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao desativar produto no banco de dados.")

# ===== Movimentação Estoque =====
def registrar_movimentacao(db: Session, mov: schemas.MovimentacaoEstoqueCreate):
    # Validações básicas
    if mov.quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    
    if mov.valor_unitario <= 0:
        raise ValueError("Valor unitário deve ser maior que zero.")
    
    if mov.tipo not in [t.value for t in TipoMovimentacao]:
        raise ValueError(f"Tipo de movimentação inválido. Deve ser um dos: {[t.value for t in TipoMovimentacao]}")
    
    produto = get_produto(db, mov.produto_id)
    if not produto:
        raise ValueError("Produto não encontrado.")
    
    usuario = get_user_by_id(db, mov.usuario_id)
    if not usuario:
        raise ValueError("Usuário não encontrado.")
    
    if mov.cliente_id:
        cliente = get_cliente(db, mov.cliente_id)
        if not cliente:
            raise ValueError("Cliente não encontrado.")
    
    # Lógica específica para tipo de movimentação
    if mov.tipo == TipoMovimentacao.saida:
        if produto.estoque_quantidade < mov.quantidade:
            raise ValueError("Estoque insuficiente.")
        produto.estoque_quantidade -= mov.quantidade
    else:
        produto.estoque_quantidade += mov.quantidade

    # Atualiza valor unitário se for entrada e valor diferente
    if mov.tipo == TipoMovimentacao.entrada and mov.valor_unitario != produto.valor_unitario:
        produto.valor_unitario = mov.valor_unitario

    db_mov = entities.MovimentacaoEstoque(
        produto_id=mov.produto_id,
        usuario_id=mov.usuario_id,
        cliente_id=mov.cliente_id,
        tipo=mov.tipo,
        quantidade=mov.quantidade,
        valor_unitario=mov.valor_unitario,
        forma_pagamento=mov.forma_pagamento,
        observacao=mov.observacao,
        data=datetime.utcnow(),
    )
    db.add(db_mov)

    try:
        db.commit()
        db.refresh(db_mov)
        
        # Cria lançamento financeiro correspondente
        valor_total = mov.quantidade * mov.valor_unitario
        tipo_financeiro = TipoMovimentacao.entrada if mov.tipo == TipoMovimentacao.saida else TipoMovimentacao.saida
        categoria = CategoriaFinanceira.venda if mov.tipo == TipoMovimentacao.saida else CategoriaFinanceira.compra
        
        create_lancamento_financeiro(db, {
            "tipo": tipo_financeiro,
            "categoria": categoria,
            "valor": valor_total,
            "descricao": f"{mov.tipo} de produto - ID {db_mov.id}",
            "data": datetime.utcnow(),
            "nota_fiscal_id": None,
            "cliente_id": mov.cliente_id
        })
        
        return db_mov
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao registrar movimentação no banco de dados.")

# ===== Cliente =====
def create_cliente(db: Session, cliente: schemas.ClienteCreate):
    # Validações
    if cliente.documento and not validar_documento(cliente.documento):
        raise ValueError("Documento inválido. CPF deve ter 11 dígitos ou CNPJ 14 dígitos.")
    
    db_cliente = entities.Cliente(**cliente.dict())
    db.add(db_cliente)
    try:
        db.commit()
        db.refresh(db_cliente)
        return db_cliente
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar cliente no banco de dados.")

def get_cliente(db: Session, cliente_id: int):
    return db.query(entities.Cliente).filter(entities.Cliente.id == cliente_id, entities.Cliente.ativo == True).first()

def get_clientes(db: Session):
    return db.query(entities.Cliente).filter(entities.Cliente.ativo == True).all()

def update_cliente(db: Session, cliente_id: int, cliente_data: schemas.ClienteBase):
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise ValueError("Cliente não encontrado ou inativo.")
    
    # Validações
    if cliente_data.documento and not validar_documento(cliente_data.documento):
        raise ValueError("Documento inválido. CPF deve ter 11 dígitos ou CNPJ 14 dígitos.")
    
    for field, value in cliente_data.dict(exclude_unset=True).items():
        setattr(cliente, field, value)
    cliente.atualizado_em = datetime.utcnow()
    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao atualizar cliente no banco de dados.")

def delete_cliente(db: Session, cliente_id: int):
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise ValueError("Cliente não encontrado ou já inativo.")
    
    cliente.ativo = False
    cliente.atualizado_em = datetime.utcnow()
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao desativar cliente no banco de dados.")

# ===== Nota Fiscal =====
# def create_nota_fiscal(db: Session, nota: schemas.NotaFiscalCreate):
#     # Validações
#     if nota.chave_acesso:
#         existing = db.query(entities.NotaFiscal).filter(entities.NotaFiscal.chave_acesso == nota.chave_acesso).first()
#         if existing:
#             raise ValueError("Chave de acesso já cadastrada.")
    
#     if nota.status not in [s.value for s in StatusNota]:
#         raise ValueError(f"Status inválido. Deve ser um dos: {[s.value for s in StatusNota]}")
    
#     if nota.valor_total <= 0:
#         raise ValueError("Valor total deve ser maior que zero.")
    
#     cliente = get_cliente(db, nota.cliente_id)
#     if not cliente:
#         raise ValueError("Cliente não encontrado.")
    
#     db_nota = entities.NotaFiscal(
#         cliente_id=nota.cliente_id,
#         data_emissao=nota.data_emissao or datetime.utcnow(),
#         valor_total=nota.valor_total,
#         status=nota.status,
#         chave_acesso=nota.chave_acesso,
#         observacao=nota.observacao,
#     )
#     db.add(db_nota)
#     try:
#         db.commit()
#         db.refresh(db_nota)

#         # Valida e insere os itens da nota
#         valor_total_calculado = Decimal('0')
#         for item in nota.itens:
#             produto = get_produto(db, item.produto_id)
#             if not produto:
#                 raise ValueError(f"Produto ID {item.produto_id} não encontrado.")
            
#             if item.quantidade <= 0:
#                 raise ValueError(f"Quantidade inválida para produto {produto.nome}.")
            
#             if item.valor_unitario <= 0:
#                 raise ValueError(f"Valor unitário inválido para produto {produto.nome}.")
            
#             # Verifica estoque para saída (venda)
#             if produto.estoque_quantidade < item.quantidade:
#                 raise ValueError(f"Estoque insuficiente para produto {produto.nome}.")

#             # Atualiza estoque (saída)
#             produto.estoque_quantidade -= item.quantidade

#             valor_item = Decimal(str(item.quantidade)) * Decimal(str(item.valor_unitario))
#             valor_total_calculado += valor_item

#             db_item = entities.NotaFiscalItem(
#                 nota_id=db_nota.id,
#                 produto_id=item.produto_id,
#                 quantidade=item.quantidade,
#                 valor_unitario=item.valor_unitario,
#                 valor_total=float(valor_item),
#             )
#             db.add(db_item)

#         # Verifica se o valor total bate com a soma dos itens
#         if abs(valor_total_calculado - Decimal(str(nota.valor_total))) > Decimal('0.01'):
#             db.rollback()
#             raise ValueError(f"Valor total da nota ({nota.valor_total}) não corresponde à soma dos itens ({float(valor_total_calculado)}).")

#         db.commit()
        
#         # Cria lançamento financeiro para a venda
#         create_lancamento_financeiro(db, {
#             "tipo": "entrada",
#             "categoria": "venda",
#             "valor": float(valor_total_calculado),
#             "descricao": f"Venda - Nota Fiscal {db_nota.id}",
#             "data": db_nota.data_emissao,
#             "nota_fiscal_id": db_nota.id,
#             "cliente_id": nota.cliente_id
#         })
        
#         return db_nota
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise ValueError("Erro ao criar nota fiscal no banco de dados.")

def create_nota_fiscal(db: Session, nota: dict) -> entities.NotaFiscal:
    """Cria uma nova nota fiscal"""
    # Validações básicas
    if nota["valor_total"] <= 0:
        raise ValueError("Valor total deve ser maior que zero.")
    
    if nota.get("chave_acesso"):
        existing = db.query(entities.NotaFiscal).filter(entities.NotaFiscal.chave_acesso == nota["chave_acesso"]).first()
        if existing:
            raise ValueError("Chave de acesso já cadastrada.")
    
    # Cria a nota fiscal
    db_nota = entities.NotaFiscal(
        cliente_id=nota["cliente_id"],
        data_emissao=datetime.utcnow(),
        valor_total=nota["valor_total"],
        status="emitida",
        chave_acesso=nota.get("chave_acesso"),
        observacao=nota.get("observacao", ""),
        forma_pagamento=nota.get("forma_pagamento")  # Este campo agora existe no modelo
    )
    
    db.add(db_nota)
    try:
        db.commit()
        db.refresh(db_nota)
        
        # Adiciona os itens da nota fiscal
        for item in nota["itens"]:
            db_item = entities.NotaFiscalItem(
                nota_id=db_nota.id,
                produto_id=item["produto_id"],
                quantidade=item["quantidade"],
                valor_unitario=item["valor_unitario"],
                valor_total=item["valor_total"]
            )
            db.add(db_item)
        
        db.commit()
        return db_nota
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar nota fiscal no banco de dados.")

def get_nota_fiscal(db: Session, nota_id: int):
    nota = db.query(entities.NotaFiscal).filter(entities.NotaFiscal.id == nota_id).first()
    if nota:
        nota.itens = db.query(entities.NotaFiscalItem).filter(entities.NotaFiscalItem.nota_id == nota_id).all()
    return nota

def get_notas_fiscais(db: Session):
    notas = db.query(entities.NotaFiscal).all()
    for nota in notas:
        nota.itens = db.query(entities.NotaFiscalItem).filter(entities.NotaFiscalItem.nota_id == nota.id).all()
    return notas

# ===== Financeiro =====
def create_lancamento_financeiro(db: Session, lancamento: dict) -> entities.Financeiro:
    """Cria um novo lançamento financeiro"""
    # Validações
    if lancamento["valor"] <= 0:
        raise ValueError("Valor deve ser maior que zero.")
    
    if lancamento["tipo"] not in [t.value for t in TipoMovimentacao]:
        raise ValueError(f"Tipo de lançamento inválido. Deve ser um dos: {[t.value for t in TipoMovimentacao]}")
    
    if lancamento["categoria"] not in [c.value for c in CategoriaFinanceira]:
        raise ValueError(f"Categoria inválida. Deve ser um dos: {[c.value for c in CategoriaFinanceira]}")
    
    if lancamento.get("nota_fiscal_id"):
        nota = get_nota_fiscal(db, lancamento["nota_fiscal_id"])
        if not nota:
            raise ValueError("Nota fiscal não encontrada.")
    
    if lancamento.get("cliente_id"):
        cliente = get_cliente(db, lancamento["cliente_id"])
        if not cliente:
            raise ValueError("Cliente não encontrado.")
    
    # Cria o objeto Financeiro
    db_lancamento = entities.Financeiro(
        tipo=lancamento["tipo"],
        categoria=lancamento["categoria"],
        valor=lancamento["valor"],
        descricao=lancamento.get("descricao", ""),
        data=lancamento.get("data", datetime.utcnow()),
        nota_fiscal_id=lancamento.get("nota_fiscal_id"),
        cliente_id=lancamento.get("cliente_id"),
    )
    
    db.add(db_lancamento)
    try:
        db.commit()
        db.refresh(db_lancamento)
        return db_lancamento
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar lançamento financeiro no banco de dados.")

def get_lancamento_financeiro(db: Session, lancamento_id: int) -> Optional[entities.Financeiro]:
    """Obtém um lançamento financeiro pelo ID"""
    return db.query(entities.Financeiro).filter(entities.Financeiro.id == lancamento_id).first()

def get_lancamentos_financeiros(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None
) -> List[entities.Financeiro]:
    """Lista todos os lançamentos financeiros com filtros opcionais"""
    query = db.query(entities.Financeiro)
    
    if tipo:
        query = query.filter(entities.Financeiro.tipo == tipo)
    if categoria:
        query = query.filter(entities.Financeiro.categoria == categoria)
    if data_inicio:
        query = query.filter(entities.Financeiro.data >= data_inicio)
    if data_fim:
        query = query.filter(entities.Financeiro.data <= data_fim)
    
    return query.offset(skip).limit(limit).all()

def update_lancamento_financeiro(
    db: Session, 
    lancamento_id: int, 
    lancamento_data: dict
) -> Optional[entities.Financeiro]:
    """Atualiza um lançamento financeiro existente"""
    lancamento = get_lancamento_financeiro(db, lancamento_id)
    if not lancamento:
        return None
    
    # Validações
    if lancamento_data.get("valor") and lancamento_data["valor"] <= 0:
        raise ValueError("Valor deve ser maior que zero.")
    
    if lancamento_data.get("tipo") and lancamento_data["tipo"] not in [t.value for t in TipoMovimentacao]:
        raise ValueError(f"Tipo de lançamento inválido. Deve ser um dos: {[t.value for t in TipoMovimentacao]}")
    
    if lancamento_data.get("categoria") and lancamento_data["categoria"] not in [c.value for c in CategoriaFinanceira]:
        raise ValueError(f"Categoria inválida. Deve ser um dos: {[c.value for c in CategoriaFinanceira]}")
    
    # Atualiza os campos
    for field, value in lancamento_data.items():
        setattr(lancamento, field, value)
    
    try:
        db.commit()
        db.refresh(lancamento)
        return lancamento
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao atualizar lançamento financeiro no banco de dados.")

def delete_lancamento_financeiro(db: Session, lancamento_id: int) -> bool:
    """Remove um lançamento financeiro"""
    lancamento = get_lancamento_financeiro(db, lancamento_id)
    if not lancamento:
        return False
    
    try:
        db.delete(lancamento)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao remover lançamento financeiro no banco de dados.")