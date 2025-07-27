from zoneinfo import ZoneInfo
from flask_login import current_user
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import schemas
from app.models import entities
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict

class TipoUsuario(str, Enum):
    admin = "admin"
    operador = "operador"

class TipoMovimentacao(str, Enum):
    entrada = "entrada"
    saida = "saida"

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
    pix_maquineta = "pix_maquineta"
    dinheiro = "dinheiro"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"
    a_prazo = "a_prazo"

class UnidadeMedida(str, Enum):
    kg = "kg"
    saco = "saco"
    unidade = "unidade"

class TipoDesconto(str, Enum):
    fixo = "fixo"
    percentual = "percentual"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== Utilitários =====
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

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

# ===== Caixa =====
def abrir_caixa(db: Session, operador_id: int, valor_abertura: Decimal, observacao: str = "") -> entities.Caixa:
    """Abre um novo caixa com o valor de abertura especificado"""
    if valor_abertura <= 0:
        raise ValueError("Valor de abertura deve ser maior que zero")
    
    # Verifica se já existe caixa aberto
    caixa_aberto = get_caixa_aberto(db)
    if caixa_aberto:
        raise ValueError("Já existe um caixa aberto")
    
    db_caixa = entities.Caixa(
        operador_id=operador_id,
        valor_abertura=valor_abertura,
        status=StatusCaixa.aberto,
        observacoes=observacao
    )
    
    db.add(db_caixa)
    try:
        db.commit()
        db.refresh(db_caixa)
        
        # Cria lançamento financeiro de abertura
        create_lancamento_financeiro(db, {
            "tipo": TipoMovimentacao.entrada,
            "categoria": CategoriaFinanceira.abertura_caixa,
            "valor": float(valor_abertura),
            "descricao": f"Abertura de caixa - ID {db_caixa.id}",
            "data": datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            "caixa_id": db_caixa.id
        })
        
        return db_caixa
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao abrir caixa no banco de dados")

def fechar_caixa(db: Session, operador_id: int, valor_fechamento: Decimal, observacao: str = "") -> entities.Caixa:
    """Fecha o caixa atual com o valor de fechamento especificado"""
    if valor_fechamento <= 0:
        raise ValueError("Valor de fechamento deve ser maior que zero")
    
    caixa = get_caixa_aberto(db)
    if not caixa:
        raise ValueError("Nenhum caixa aberto encontrado")
    
    # Atualiza dados do caixa
    caixa.operador_id = operador_id
    caixa.valor_fechamento = valor_fechamento
    caixa.data_fechamento = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    caixa.status = StatusCaixa.fechado
    caixa.observacoes = observacao
    
    try:
        db.commit()
        
        # Cria lançamento financeiro de fechamento
        create_lancamento_financeiro(db, {
            "tipo": TipoMovimentacao.saida,
            "categoria": CategoriaFinanceira.fechamento_caixa,
            "valor": float(valor_fechamento),
            "descricao": f"Fechamento de caixa - ID {caixa.id}",
            "data": datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            "caixa_id": caixa.id
        })
        
        return caixa
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao fechar caixa no banco de dados")

def get_caixa_aberto(db: Session) -> Optional[entities.Caixa]:
    """Retorna o caixa atualmente aberto, se existir"""
    return db.query(entities.Caixa).filter(entities.Caixa.status == StatusCaixa.aberto).first()

def get_caixa_by_id(db: Session, caixa_id: int) -> Optional[entities.Caixa]:
    """Retorna um caixa pelo ID"""
    return db.query(entities.Caixa).filter(entities.Caixa.id == caixa_id).first()

def get_caixas(db: Session, skip: int = 0, limit: int = 100) -> List[entities.Caixa]:
    """Lista todos os caixas"""
    return db.query(entities.Caixa).order_by(entities.Caixa.data_abertura.desc()).offset(skip).limit(limit).all()

def get_ultimo_caixa_fechado(db: Session) -> Optional[entities.Caixa]:
    """Retorna o último caixa fechado"""
    return db.query(entities.Caixa)\
            .filter(entities.Caixa.status == StatusCaixa.fechado)\
            .order_by(entities.Caixa.data_fechamento.desc())\
            .first()
            
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
    if not validar_cpf(user.cpf):
        raise ValueError("CPF inválido. Deve conter 11 dígitos.")
    
    if get_user_by_cpf(db, user.cpf):
        raise ValueError("CPF já cadastrado.")
    
    if user.tipo not in [t.value for t in TipoUsuario]:
        raise ValueError(f"Tipo de usuário inválido. Deve ser um dos: {[t.value for t in TipoUsuario]}")
    
    if len(user.senha) < 6:
        raise ValueError("Senha deve ter pelo menos 6 caracteres.")
    
    hashed_password = hash_password(user.senha)

    db_user = entities.Usuario(
        nome=user.nome,
        cpf=user.cpf,
        senha_hash=hashed_password,
        tipo=user.tipo,
        status=user.status if user.status is not None else True,
        criado_em=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        observacoes=user.observacoes or ""
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
    
    update_data = produto_data.dict(exclude_unset=True)
    
    if "unidade" in update_data and update_data["unidade"] not in [u.value for u in UnidadeMedida]:
        raise ValueError(f"Unidade de medida inválida. Deve ser um dos: {[u.value for u in UnidadeMedida]}")
    
    if "valor_unitario" in update_data and update_data["valor_unitario"] <= 0:
        raise ValueError("Valor unitário deve ser maior que zero.")
    
    if "estoque_quantidade" in update_data and update_data["estoque_quantidade"] < 0:
        raise ValueError("Quantidade em estoque não pode ser negativa.")
    
    for field, value in update_data.items():
        setattr(produto, field, value)
    
    produto.atualizado_em = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    
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
    produto.atualizado_em = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao desativar produto no banco de dados.")

# ===== Movimentação Estoque =====
def registrar_movimentacao(db: Session, mov: schemas.MovimentacaoEstoqueCreate):
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
    
    caixa = get_caixa_by_id(db, mov.caixa_id)
    if not caixa:
        raise ValueError("Caixa não encontrado.")
    
    if mov.tipo == TipoMovimentacao.saida:
        if produto.estoque_quantidade < mov.quantidade:
            raise ValueError("Estoque insuficiente.")
        produto.estoque_quantidade -= mov.quantidade
    else:
        produto.estoque_quantidade += mov.quantidade

    if mov.tipo == TipoMovimentacao.entrada and mov.valor_unitario != produto.valor_unitario:
        produto.valor_unitario = mov.valor_unitario

    db_mov = entities.MovimentacaoEstoque(
        produto_id=mov.produto_id,
        usuario_id=mov.usuario_id,
        cliente_id=mov.cliente_id,
        caixa_id=mov.caixa_id,
        tipo=mov.tipo,
        quantidade=mov.quantidade,
        valor_unitario=mov.valor_unitario,
        valor_recebido=mov.valor_recebido,
        troco=mov.troco,
        forma_pagamento=mov.forma_pagamento,
        observacao=mov.observacao,
        data=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
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
            "valor": float(valor_total),
            "descricao": f"{mov.tipo} de produto - ID {db_mov.id}",
            "data": datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            "nota_fiscal_id": None,
            "cliente_id": mov.cliente_id,
            "caixa_id": mov.caixa_id
        })
        
        return db_mov
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao registrar movimentação no banco de dados.")

# ===== Cliente =====
def create_cliente(db: Session, cliente: schemas.ClienteCreate):
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
    return db.query(entities.Cliente).filter(
        entities.Cliente.id == cliente_id
    ).first()

def get_clientes(db: Session):
    return db.query(entities.Cliente).filter(entities.Cliente.ativo == True).all()

def get_clientes_all(db: Session):
    return db.query(entities.Cliente).all()

def update_cliente(db: Session, cliente_id: int, cliente_data: schemas.ClienteBase):
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise ValueError("Cliente não encontrado ou inativo.")
    
    if cliente_data.documento and not validar_documento(cliente_data.documento):
        raise ValueError("Documento inválido. CPF deve ter 11 dígitos ou CNPJ 14 dígitos.")
    
    for field, value in cliente_data.dict(exclude_unset=True).items():
        setattr(cliente, field, value)
    cliente.atualizado_em = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
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
    cliente.atualizado_em = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao desativar cliente no banco de dados.")

# ===== Nota Fiscal =====
def create_nota_fiscal(db: Session, nota: dict) -> entities.NotaFiscal:
    """Cria uma nova nota fiscal com os itens associados"""
    try:
        # Validação básica
        if nota["valor_total"] <= 0:
            raise ValueError("Valor total deve ser maior que zero")
            
        if not nota.get("itens") or len(nota["itens"]) == 0:
            raise ValueError("Nota fiscal deve conter pelo menos um item")

        # Verifica caixa
        caixa = get_caixa_by_id(db, nota["caixa_id"])
        if not caixa:
            raise ValueError("Caixa não encontrado")

        # Cria a nota fiscal
        db_nota = entities.NotaFiscal(
            cliente_id=nota["cliente_id"],
            operador_id=current_user.id,  # Usa o usuário atual
            caixa_id=nota["caixa_id"],
            data_emissao=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            valor_total=nota["valor_total"],
            valor_desconto=nota.get("valor_desconto", 0),
            tipo_desconto=nota.get("tipo_desconto"),
            status=StatusNota.emitida,
            observacao=nota.get("observacao", ""),
            forma_pagamento=nota["forma_pagamento"],
            valor_recebido=nota.get("valor_recebido", nota["valor_total"]),
            troco=nota.get("troco", 0),
            entrega_id=nota.get("entrega_id")
        )
        
        db.add(db_nota)
        db.commit()
        db.refresh(db_nota)

        # Adiciona os itens
        for item in nota["itens"]:
            db_item = entities.NotaFiscalItem(
                nota_id=db_nota.id,
                produto_id=item["produto_id"],
                quantidade=item["quantidade"],
                valor_unitario=item["valor_unitario"],
                valor_total=item["valor_total"],
                desconto_aplicado=item.get("desconto_aplicado", 0),
                tipo_desconto=item.get("tipo_desconto", "fixo")
            )
            db.add(db_item)
        
        db.commit()
        return db_nota
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Erro ao criar nota fiscal no banco de dados: {str(e)}")

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

# ===== Entrega =====
def create_entrega(db: Session, entrega_data: dict) -> entities.Entrega:
    """Cria um novo registro de entrega"""
    try:
        # Validação básica
        required_fields = ['logradouro', 'numero', 'bairro', 'cidade', 'estado', 'cep']
        for field in required_fields:
            if field not in entrega_data:
                raise ValueError(f"Campo obrigatório faltando: {field}")
        
        db_entrega = entities.Entrega(**entrega_data)
        db.add(db_entrega)
        db.commit()
        db.refresh(db_entrega)
        return db_entrega
    except Exception as e:
        db.rollback()
        raise ValueError(f"Erro ao criar entrega: {str(e)}")

# ===== Financeiro =====
def create_lancamento_financeiro(db: Session, lancamento: dict) -> entities.Financeiro:
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
    
    if lancamento.get("caixa_id"):
        caixa = get_caixa_by_id(db, lancamento["caixa_id"])
        if not caixa:
            raise ValueError("Caixa não encontrado.")
    
    db_lancamento = entities.Financeiro(
        tipo=lancamento["tipo"],
        categoria=lancamento["categoria"],
        valor=lancamento["valor"],
        valor_desconto=lancamento.get("valor_desconto", 0),
        descricao=lancamento.get("descricao", ""),
        data=lancamento.get("data", datetime.now(tz=ZoneInfo('America/Sao_Paulo'))),
        nota_fiscal_id=lancamento.get("nota_fiscal_id"),
        cliente_id=lancamento.get("cliente_id"),
        caixa_id=lancamento.get("caixa_id")
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
    return db.query(entities.Financeiro).filter(entities.Financeiro.id == lancamento_id).first()

def get_lancamentos_financeiros(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    caixa_id: Optional[int] = None
) -> List[entities.Financeiro]:
    query = db.query(entities.Financeiro)
    
    if tipo:
        query = query.filter(entities.Financeiro.tipo == tipo)
    if categoria:
        query = query.filter(entities.Financeiro.categoria == categoria)
    if data_inicio:
        query = query.filter(entities.Financeiro.data >= data_inicio)
    if data_fim:
        query = query.filter(entities.Financeiro.data <= data_fim)
    if caixa_id:
        query = query.filter(entities.Financeiro.caixa_id == caixa_id)
    
    return query.order_by(entities.Financeiro.data.desc()).offset(skip).limit(limit).all()

def update_lancamento_financeiro(
    db: Session, 
    lancamento_id: int, 
    lancamento_data: dict
) -> Optional[entities.Financeiro]:
    lancamento = get_lancamento_financeiro(db, lancamento_id)
    if not lancamento:
        return None
    
    if lancamento_data.get("valor") and lancamento_data["valor"] <= 0:
        raise ValueError("Valor deve ser maior que zero.")
    
    if lancamento_data.get("tipo") and lancamento_data["tipo"] not in [t.value for t in TipoMovimentacao]:
        raise ValueError(f"Tipo de lançamento inválido. Deve ser um dos: {[t.value for t in TipoMovimentacao]}")
    
    if lancamento_data.get("categoria") and lancamento_data["categoria"] not in [c.value for c in CategoriaFinanceira]:
        raise ValueError(f"Categoria inválida. Deve ser um dos: {[c.value for c in CategoriaFinanceira]}")
    
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

# ===== Vendas =====
def registrar_venda_completa(db: Session, dados: dict, operador_id: int, caixa_id: int):
    try:
        # ----------------------
        # Salva Entrega (se houver)
        # ----------------------
        entrega = None
        if 'entrega' in dados and dados['entrega']:
            entrega_data = dados['entrega']
            entrega = entities.Entrega(
                logradouro=entrega_data['logradouro'],
                numero=entrega_data['numero'],
                complemento=entrega_data.get('complemento'),
                bairro=entrega_data['bairro'],
                cidade=entrega_data['cidade'],
                estado=entrega_data['estado'],
                cep=entrega_data['cep'],
                instrucoes=entrega_data.get('instrucoes'),
                sincronizado=False
            )
            db.add(entrega)
            db.flush()

        # ----------------------
        # Verifica estoque antes de processar a venda
        # ----------------------
        produtos_para_atualizar = {}
        for item in dados['itens']:
            produto_id = item['produto_id']
            quantidade = Decimal(str(item['quantidade']))
            
            produto = db.query(entities.Produto).filter(
                entities.Produto.id == produto_id
            ).with_for_update().one_or_none()
            
            if not produto:
                raise ValueError(f"Produto com ID {produto_id} não encontrado.")
            
            if produto.estoque_quantidade < quantidade:
                raise ValueError(
                    f"Estoque insuficiente para o produto '{produto.nome}'. "
                    f"Quantidade solicitada: {quantidade}, disponível: {produto.estoque_quantidade}"
                )
            
            produtos_para_atualizar[produto_id] = {
                'produto': produto,
                'quantidade': quantidade
            }

        # ----------------------
        # Calcula valores totais e descontos
        # ----------------------
        total_geral = Decimal("0.00")
        total_descontos_itens = Decimal("0.00")  # Soma dos descontos aplicados nos itens
        itens_processados = []

        for item in dados['itens']:
            quantidade = Decimal(str(item['quantidade']))
            valor_unitario = Decimal(str(item['valor_unitario']))

            # Aplica desconto por item
            desconto_aplicado = Decimal(str(item.get('desconto_aplicado', 0)))
            tipo_desconto = item.get('tipo_desconto')

            if tipo_desconto == TipoDesconto.percentual:
                desconto_aplicado = (valor_unitario * desconto_aplicado) / Decimal("100.00")

            total_descontos_itens += desconto_aplicado * quantidade

            valor_unitario_com_desconto = valor_unitario - desconto_aplicado
            valor_total_item = valor_unitario_com_desconto * quantidade

            total_geral += valor_total_item

            itens_processados.append({
                **item,
                "valor_total": valor_total_item,
                "valor_unitario": valor_unitario,
                "desconto_aplicado": desconto_aplicado,
                "tipo_desconto": tipo_desconto,
                "quantidade": quantidade
            })

        # Desconto adicional (geral) da venda
        valor_desconto_total = Decimal(str(dados.get("desconto", 0))) + total_descontos_itens
        valor_recebido = Decimal(str(dados.get("valor_recebido", 0)))
        troco = valor_recebido - (total_geral - valor_desconto_total)

        # ----------------------
        # Cria Nota Fiscal
        # ----------------------
        nota = entities.NotaFiscal(
            cliente_id=dados['cliente_id'],
            operador_id=operador_id,
            caixa_id=caixa_id,
            entrega_id=entrega.id if entrega else None,
            valor_total=total_geral,
            valor_desconto=valor_desconto_total,  # Aqui deve ir o desconto total (itens + desconto geral)
            tipo_desconto=dados.get('tipo_desconto'),
            status=StatusNota.emitida,
            observacao=dados.get('observacao'),
            forma_pagamento=dados['forma_pagamento'],
            valor_recebido=valor_recebido,
            troco=troco,
            sincronizado=False,
            data_emissao=datetime.now()
        )
        db.add(nota)
        db.flush()

        # ----------------------
        # Processa cada item da nota
        # ----------------------
        for item in itens_processados:
            produto_id = item['produto_id']
            quantidade = item['quantidade']
            desconto_aplicado = item['desconto_aplicado']
            tipo_desconto = item['tipo_desconto']

            # Salva item da nota
            nota_item = entities.NotaFiscalItem(
                nota_id=nota.id,
                produto_id=produto_id,
                quantidade=quantidade,
                valor_unitario=item['valor_unitario'],
                valor_total=item['valor_total'],
                desconto_aplicado=desconto_aplicado,
                tipo_desconto=tipo_desconto,
                sincronizado=False
            )
            db.add(nota_item)

            # Movimentação de estoque
            movimentacao = entities.MovimentacaoEstoque(
                produto_id=produto_id,
                usuario_id=operador_id,
                cliente_id=dados['cliente_id'],
                caixa_id=caixa_id,
                tipo=TipoMovimentacao.saida,
                quantidade=quantidade,
                valor_unitario=item['valor_unitario'],
                valor_recebido=valor_recebido,
                troco=troco,
                forma_pagamento=dados['forma_pagamento'],
                observacao=dados.get('observacao'),
                sincronizado=False
            )
            db.add(movimentacao)

            # Atualiza estoque do produto
            produto_info = produtos_para_atualizar[produto_id]
            produto_info['produto'].estoque_quantidade -= produto_info['quantidade']

        # ----------------------
        # Lançamento financeiro
        # ----------------------
        financeiro = entities.Financeiro(
            tipo=TipoMovimentacao.entrada,
            categoria=CategoriaFinanceira.venda,
            valor=nota.valor_total,
            valor_desconto=nota.valor_desconto,  # Usa o mesmo valor_desconto da nota fiscal
            descricao=f"Venda para cliente ID {dados['cliente_id']}",
            data=datetime.now(),
            nota_fiscal_id=nota.id,
            cliente_id=dados['cliente_id'],
            caixa_id=caixa_id,
            sincronizado=False
        )
        db.add(financeiro)

        # Confirma todas as alterações
        db.commit()
        return nota.id

    except Exception as e:
        db.rollback()
        print(f"Erro ao registrar venda: {str(e)}")
        raise