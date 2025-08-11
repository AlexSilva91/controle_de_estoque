from zoneinfo import ZoneInfo
from flask import json
from flask_login import current_user
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import schemas
from app.models import entities
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func
from typing import Dict, Any, List, Union, Tuple


from app.models.entities import (
    Caixa,
    Financeiro,
    NotaFiscal,
    NotaFiscalItem,
    MovimentacaoEstoque,
    PagamentoNotaFiscal,
    StatusCaixa,
    StatusNota,
    StatusPagamento,
    UnidadeMedida, 
    FormaPagamento
)

from app.utils.conversor_unidade import converter_quantidade
from app.models.entities import (
    TipoDesconto, TipoEstoque, TipoMovimentacao, TipoUsuario, CategoriaFinanceira, 
)

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
def abrir_caixa(db: Session, operador_id: int, valor_abertura: Decimal, observacao: str = None):
    """
    Abre um novo caixa para um operador específico.
    Verifica se o operador já tem um caixa aberto antes de criar um novo.
    """
    # Verifica se o operador já tem um caixa aberto
    caixa_existente = get_caixa_aberto(db, operador_id=operador_id)
    if caixa_existente:
        raise ValueError(f"Operador já possui um caixa aberto (Caixa #{caixa_existente.id})")
    
    try:
        # Cria o novo caixa
        novo_caixa = Caixa(
            operador_id=operador_id,
            valor_abertura=valor_abertura,
            data_abertura=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            status=StatusCaixa.aberto,
            observacoes=observacao
        )
        
        db.add(novo_caixa)
        db.flush()  # Para obter o ID antes do commit
        
        # Cria registro financeiro de abertura
        abertura_financeiro = Financeiro(
            tipo=TipoMovimentacao.entrada,
            categoria=CategoriaFinanceira.abertura_caixa,
            valor=valor_abertura,
            descricao=f"Abertura do caixa #{novo_caixa.id}",
            caixa_id=novo_caixa.id,
            data=novo_caixa.data_abertura
        )
        
        db.add(abertura_financeiro)
        db.commit()
        
        return novo_caixa
        
    except Exception as e:
        db.rollback()
        raise e
    
def fechar_caixa(db: Session, operador_id: int, valor_fechamento: Decimal, observacao: str = "") -> entities.Caixa:
    """
    Fecha o caixa atual do operador específico com o valor de fechamento especificado.
    
    Args:
        db (Session): Sessão do banco de dados
        operador_id (int): ID do operador que está fechando o caixa
        valor_fechamento (Decimal): Valor de fechamento informado pelo operador
        observacao (str, optional): Observações do operador sobre o fechamento
    
    Returns:
        entities.Caixa: O caixa fechado
        
    Raises:
        ValueError: Se valor_fechamento <= 0, se nenhum caixa do operador estiver aberto,
                   ou se houver erro no banco de dados
    """
    if valor_fechamento <= 0:
        raise ValueError("Valor de fechamento deve ser maior que zero")
    
    # Busca o caixa aberto APENAS do operador específico
    caixa = get_caixa_aberto(db, operador_id)
    if not caixa:
        raise ValueError("Nenhum caixa aberto encontrado para este operador")
    
    # Validação adicional: verifica se o caixa realmente pertence ao operador
    if caixa.operador_id != operador_id:
        raise ValueError("Operador não autorizado a fechar este caixa")
    
    # Atualiza dados do caixa
    caixa.valor_fechamento = valor_fechamento
    caixa.data_fechamento = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    caixa.status = StatusCaixa.fechado
    caixa.observacoes = observacao
    caixa.sincronizado = False
    
    try:
        db.commit()
        
        # Cria lançamento financeiro de fechamento
        lancamento_data = {
            "tipo": TipoMovimentacao.saida,
            "categoria": CategoriaFinanceira.fechamento_caixa,
            "valor": float(valor_fechamento),
            "descricao": "Fechamento de caixa",
            "caixa_id": caixa.id,
            "data": datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
        }
        
        # Cria o objeto FinanceiroCreate a partir do dicionário
        lancamento = schemas.FinanceiroCreate(**lancamento_data)
        create_lancamento_financeiro(db, lancamento)
        
        return caixa
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao fechar caixa no banco de dados")

def get_caixa_aberto(db: Session, operador_id: int):
    """
    Retorna o caixa aberto para um operador específico.
    
    Args:
        db (Session): Sessão do banco de dados
        operador_id (int): ID do operador (obrigatório)
    
    Returns:
        Caixa: O caixa aberto do operador ou None se não encontrado
    """
    return db.query(Caixa).filter(
        Caixa.status == StatusCaixa.aberto,
        Caixa.operador_id == operador_id
    ).first()

def get_caixa_by_id(db: Session, caixa_id: int) -> Optional[entities.Caixa]:
    """Retorna um caixa pelo ID"""
    return db.query(entities.Caixa).filter(entities.Caixa.id == caixa_id).first()

def get_caixas(db: Session, skip: int = 0, limit: int = 100) -> List[entities.Caixa]:
    """Lista todos os caixas"""
    return db.query(entities.Caixa).order_by(entities.Caixa.data_abertura.desc()).offset(skip).limit(limit).all()

def get_ultimo_caixa_fechado(db: Session, operador_id: int = None):
    """
    Retorna o último caixa fechado para um operador específico.
    """
    query = db.query(Caixa).filter(
        Caixa.status == StatusCaixa.fechado
    )
    
    if operador_id is not None:
        query = query.filter(Caixa.operador_id == operador_id)
        
    return query.order_by(Caixa.data_fechamento.desc()).first()

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
        observacoes=user.observacoes or "",
        sincronizado=False
    )

    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar usuário no banco de dados.")

def update_user(db: Session, user_id: int, user_data: schemas.UsuarioUpdate):
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("Usuário não encontrado")
    
    update_data = user_data.dict(exclude_unset=True)
    
    if "cpf" in update_data and not validar_cpf(update_data["cpf"]):
        raise ValueError("CPF inválido. Deve conter 11 dígitos.")
    
    if "tipo" in update_data and update_data["tipo"] not in [t.value for t in TipoUsuario]:
        raise ValueError(f"Tipo de usuário inválido. Deve ser um dos: {[t.value for t in TipoUsuario]}")
    
    if "senha" in update_data:
        if len(update_data["senha"]) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres.")
        update_data["senha_hash"] = hash_password(update_data.pop("senha"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao atualizar usuário no banco de dados.")

def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("Usuário não encontrado")
    
    try:
        db.delete(user)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao remover usuário no banco de dados.")

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
    
    db_produto = entities.Produto(
        codigo=produto.codigo,
        nome=produto.nome,
        tipo=produto.tipo,
        marca=produto.marca,
        unidade=produto.unidade,
        valor_unitario=produto.valor_unitario,
        valor_unitario_compra=produto.valor_unitario_compra,
        valor_total_compra=produto.valor_total_compra,
        imcs=produto.imcs,
        estoque_loja=produto.estoque_loja,
        estoque_deposito=produto.estoque_deposito,
        estoque_fabrica=produto.estoque_fabrica,
        estoque_minimo=produto.estoque_minimo,
        estoque_maximo=produto.estoque_maximo,
        ativo=produto.ativo,
        criado_em=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        atualizado_em=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        sincronizado=False
    )
    
    db.add(db_produto)
    try:
        db.commit()
        db.refresh(db_produto)
        return db_produto
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar produto no banco de dados.")

def update_produto(db: Session, produto_id: int, produto_data: schemas.ProdutoUpdate):
    produto = db.query(entities.Produto).filter(
        entities.Produto.id == produto_id,
        entities.Produto.ativo == True
    ).first()
    if not produto:
        raise ValueError("Produto não encontrado ou inativo.")
    
    update_data = produto_data.dict(exclude_unset=True)
    
    # Validações
    if "unidade" in update_data and update_data["unidade"] not in [u.value for u in UnidadeMedida]:
        raise ValueError(f"Unidade de medida inválida. Deve ser um dos: {[u.value for u in UnidadeMedida]}")
    
    if "valor_unitario" in update_data and update_data["valor_unitario"] <= 0:
        raise ValueError("Valor unitário deve ser maior que zero.")
    
    for field, value in update_data.items():
        setattr(produto, field, value)
    
    produto.atualizado_em = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    produto.sincronizado = False
    
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
    produto.sincronizado = False
    
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao desativar produto no banco de dados.")

def buscar_detalhes_produto(db: Session, produto_id: int):
    try:
        produto = db.get(entities.Produto, produto_id)

        if not produto:
            return None

        return {
            'id': produto.id,
            'nome': produto.nome,
            'codigo': produto.codigo,
            'preco_unitario': round(float(produto.valor_unitario), 2),
            'estoque_atual': round(float(produto.estoque_loja), 2),
            'created_at': produto.criado_em.isoformat() if produto.criado_em else None,
            'updated_at': produto.atualizado_em.isoformat() if produto.atualizado_em else None,
            'ativo': produto.ativo,
            'descontos': [
                {
                    'id': d.id,
                    'identificador': d.identificador,
                    'quantidade_minima': round(d.quantidade_minima, 2),
                    'quantidade_maxima': round(d.quantidade_maxima, 2),
                    'valor_desconto': round(float(d.valor), 2)
                }
                for d in produto.descontos
            ]
        }
    finally:
        db.close()
        
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
    
    # Atualiza estoque conforme tipo de movimentação
    if mov.tipo == TipoMovimentacao.saida:
        if mov.estoque_origem == TipoEstoque.loja and produto.estoque_loja < mov.quantidade:
            raise ValueError("Estoque insuficiente na loja.")
        elif mov.estoque_origem == TipoEstoque.deposito and produto.estoque_deposito < mov.quantidade:
            raise ValueError("Estoque insuficiente no depósito.")
        elif mov.estoque_origem == TipoEstoque.fabrica and produto.estoque_fabrica < mov.quantidade:
            raise ValueError("Estoque insuficiente na fábrica.")
        
        if mov.estoque_origem == TipoEstoque.loja:
            produto.estoque_loja -= mov.quantidade
        elif mov.estoque_origem == TipoEstoque.deposito:
            produto.estoque_deposito -= mov.quantidade
        elif mov.estoque_origem == TipoEstoque.fabrica:
            produto.estoque_fabrica -= mov.quantidade
    elif mov.tipo == TipoMovimentacao.entrada:
        if mov.estoque_destino == TipoEstoque.loja:
            produto.estoque_loja += mov.quantidade
        elif mov.estoque_destino == TipoEstoque.deposito:
            produto.estoque_deposito += mov.quantidade
        elif mov.estoque_destino == TipoEstoque.fabrica:
            produto.estoque_fabrica += mov.quantidade
        
        # Atualiza valor unitário se for entrada
        produto.valor_unitario = mov.valor_unitario

    db_mov = entities.MovimentacaoEstoque(
        produto_id=mov.produto_id,
        usuario_id=mov.usuario_id,
        cliente_id=mov.cliente_id,
        caixa_id=mov.caixa_id,
        tipo=mov.tipo,
        estoque_origem=mov.estoque_origem,
        estoque_destino=mov.estoque_destino,
        quantidade=mov.quantidade,
        valor_unitario=mov.valor_unitario,
        valor_recebido=mov.valor_recebido,
        troco=mov.troco,
        forma_pagamento=mov.forma_pagamento,
        observacao=mov.observacao,
        data=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        sincronizado=False
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
            "caixa_id": mov.caixa_id,
            "conta_receber_id": None
        })
        
        return db_mov
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao registrar movimentação no banco de dados.")

def get_movimentacao_by_id(db: Session, mov_id: int):
    return db.query(entities.MovimentacaoEstoque).filter(entities.MovimentacaoEstoque.id == mov_id).first()

def get_movimentacoes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(entities.MovimentacaoEstoque)\
            .order_by(entities.MovimentacaoEstoque.data.desc())\
            .offset(skip).limit(limit).all()

# ===== Transferência Estoque =====
def registrar_transferencia(db: Session, transf: dict):
    produto_orig = db.query(entities.Produto).filter(entities.Produto.id == transf['produto_id']).first()
    if not produto_orig:
        raise ValueError("Produto não encontrado")

    usuario = db.query(entities.Usuario).filter(entities.Usuario.id == transf['usuario_id']).first()
    if not usuario:
        raise ValueError("Usuário não encontrado")

    estoque_origem = transf['estoque_origem']
    quantidade_origem = transf['quantidade']
    converter_unidade = transf.get('converter_unidade', False)
    
    # Verificar estoque disponível
    estoque_disponivel = {
        TipoEstoque.loja: produto_orig.estoque_loja,
        TipoEstoque.deposito: produto_orig.estoque_deposito,
        TipoEstoque.fabrica: produto_orig.estoque_fabrica,
    }.get(estoque_origem, Decimal('0'))

    if estoque_disponivel < quantidade_origem:
        raise ValueError(f"Estoque insuficiente no {estoque_origem.value}. Disponível: {estoque_disponivel}")

    # Atualizar estoque original
    if estoque_origem == TipoEstoque.loja:
        produto_orig.estoque_loja -= quantidade_origem
    elif estoque_origem == TipoEstoque.deposito:
        produto_orig.estoque_deposito -= quantidade_origem
    elif estoque_origem == TipoEstoque.fabrica:
        produto_orig.estoque_fabrica -= quantidade_origem

    produto_destino = produto_orig  # Sempre o mesmo produto para transferência sem conversão
    quantidade_destino = quantidade_origem
    
    # Adicionar quantidade no estoque destino
    estoque_destino = transf['estoque_destino']
    if estoque_destino == TipoEstoque.loja:
        produto_destino.estoque_loja += quantidade_destino
    elif estoque_destino == TipoEstoque.deposito:
        produto_destino.estoque_deposito += quantidade_destino
    elif estoque_destino == TipoEstoque.fabrica:
        produto_destino.estoque_fabrica += quantidade_destino

    # Atualizar valor unitário se fornecido
    if 'valor_unitario_destino' in transf:
        produto_destino.valor_unitario = Decimal(str(transf['valor_unitario_destino']))

    # Registrar transferência
    transferencia = entities.TransferenciaEstoque(
        produto_id=produto_orig.id,
        produto_destino_id=None,  # Sem produto destino para transferência sem conversão
        usuario_id=transf['usuario_id'],
        estoque_origem=estoque_origem,
        estoque_destino=estoque_destino,
        quantidade=quantidade_origem,
        quantidade_destino=None,  # Sem quantidade destino para transferência sem conversão
        unidade_origem=produto_orig.unidade.value,
        unidade_destino=None,  # Sem unidade destino para transferência sem conversão
        peso_kg_por_saco=None,
        pacotes_por_saco=None,
        pacotes_por_fardo=None,
        observacao=transf.get('observacao', ''),
        data=datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    )

    db.add(transferencia)
    db.commit()
    db.refresh(transferencia)
    return transferencia

def get_transferencia_by_id(db: Session, transf_id: int):
    return db.query(entities.TransferenciaEstoque).filter(entities.TransferenciaEstoque.id == transf_id).first()

def get_transferencias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(entities.TransferenciaEstoque)\
            .order_by(entities.TransferenciaEstoque.data.desc())\
            .offset(skip).limit(limit).all()

# ===== Cliente =====
def create_cliente(db: Session, cliente: schemas.ClienteCreate):
    if cliente.documento and not validar_documento(cliente.documento):
        raise ValueError("Documento inválido. CPF deve ter 11 dígitos ou CNPJ 14 dígitos.")
    
    db_cliente = entities.Cliente(
        nome=cliente.nome,
        documento=cliente.documento,
        telefone=cliente.telefone,
        email=cliente.email,
        endereco=cliente.endereco,
        limite_credito=cliente.limite_credito,
        ativo=cliente.ativo,
        criado_em=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        atualizado_em=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        sincronizado=False
    )
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

def update_cliente(db: Session, cliente_id: int, cliente_data: schemas.ClienteUpdate):
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise ValueError("Cliente não encontrado ou inativo.")
    
    if cliente_data.documento and not validar_documento(cliente_data.documento):
        raise ValueError("Documento inválido. CPF deve ter 11 dígitos ou CNPJ 14 dígitos.")
    
    update_data = cliente_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(cliente, field, value)
    
    cliente.atualizado_em = datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
    cliente.sincronizado = False
    
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
    cliente.sincronizado = False
    
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao desativar cliente no banco de dados.")

# ===== Entrega =====
def create_entrega(db: Session, entrega_data: schemas.EntregaCreate) -> entities.Entrega:
    """Cria um novo registro de entrega"""
    try:
        db_entrega = entities.Entrega(
            logradouro=entrega_data.logradouro,
            numero=entrega_data.numero,
            complemento=entrega_data.complemento,
            bairro=entrega_data.bairro,
            cidade=entrega_data.cidade,
            estado=entrega_data.estado,
            cep=entrega_data.cep,
            instrucoes=entrega_data.instrucoes,
            sincronizado=False
        )
        db.add(db_entrega)
        db.commit()
        db.refresh(db_entrega)
        return db_entrega
    except Exception as e:
        db.rollback()
        raise ValueError(f"Erro ao criar entrega: {str(e)}")

def get_entrega_by_id(db: Session, entrega_id: int) -> Optional[entities.Entrega]:
    return db.query(entities.Entrega).filter(entities.Entrega.id == entrega_id).first()

def update_entrega(db: Session, entrega_id: int, entrega_data: schemas.EntregaBase) -> Optional[entities.Entrega]:
    entrega = get_entrega_by_id(db, entrega_id)
    if not entrega:
        return None
    
    update_data = entrega_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(entrega, field, value)
    
    try:
        db.commit()
        db.refresh(entrega)
        return entrega
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao atualizar entrega no banco de dados.")

def delete_entrega(db: Session, entrega_id: int) -> bool:
    entrega = get_entrega_by_id(db, entrega_id)
    if not entrega:
        return False
    
    try:
        db.delete(entrega)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao remover entrega no banco de dados.")

# ===== Nota Fiscal =====
def create_nota_fiscal(db: Session, nota: schemas.NotaFiscalCreate) -> entities.NotaFiscal:
    """Cria uma nova nota fiscal com os itens associados"""
    try:
        # Validação básica
        if nota.valor_total <= 0:
            raise ValueError("Valor total deve ser maior que zero")
            
        if not nota.itens or len(nota.itens) == 0:
            raise ValueError("Nota fiscal deve conter pelo menos um item")

        # Verifica caixa
        caixa = get_caixa_by_id(db, nota.caixa_id)
        if not caixa:
            raise ValueError("Caixa não encontrado")

        # Verifica operador
        operador = get_user_by_id(db, nota.operador_id)
        if not operador:
            raise ValueError("Operador não encontrado")

        # Verifica cliente se informado
        if nota.cliente_id:
            cliente = get_cliente(db, nota.cliente_id)
            if not cliente:
                raise ValueError("Cliente não encontrado")

        # Verifica entrega se informada
        if nota.entrega_id:
            entrega = get_entrega_by_id(db, nota.entrega_id)
            if not entrega:
                raise ValueError("Entrega não encontrada")

        # Cria a nota fiscal
        db_nota = entities.NotaFiscal(
            cliente_id=nota.cliente_id,
            operador_id=nota.operador_id,
            caixa_id=nota.caixa_id,
            entrega_id=nota.entrega_id,
            data_emissao=nota.data_emissao or datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            valor_total=nota.valor_total,
            valor_desconto=nota.valor_desconto,
            tipo_desconto=nota.tipo_desconto,
            status=nota.status,
            chave_acesso=nota.chave_acesso,
            observacao=nota.observacao,
            forma_pagamento=nota.forma_pagamento,
            valor_recebido=nota.valor_recebido,
            troco=nota.troco,
            a_prazo=nota.a_prazo,
            sincronizado=False
        )
        
        db.add(db_nota)
        db.flush()

        # Adiciona os itens e atualiza estoques
        for item in nota.itens:
            produto = get_produto(db, item.produto_id)
            if not produto:
                raise ValueError(f"Produto com ID {item.produto_id} não encontrado")
            
            # Verifica estoque
            if item.estoque_origem == TipoEstoque.loja and produto.estoque_loja < item.quantidade:
                raise ValueError(f"Estoque insuficiente na loja para o produto {produto.nome}")
            elif item.estoque_origem == TipoEstoque.deposito and produto.estoque_deposito < item.quantidade:
                raise ValueError(f"Estoque insuficiente no depósito para o produto {produto.nome}")
            elif item.estoque_origem == TipoEstoque.fabrica and produto.estoque_fabrica < item.quantidade:
                raise ValueError(f"Estoque insuficiente na fábrica para o produto {produto.nome}")
            
            # Atualiza estoque
            if item.estoque_origem == TipoEstoque.loja:
                produto.estoque_loja -= item.quantidade
            elif item.estoque_origem == TipoEstoque.deposito:
                produto.estoque_deposito -= item.quantidade
            elif item.estoque_origem == TipoEstoque.fabrica:
                produto.estoque_fabrica -= item.quantidade
            
            # Cria item da nota
            db_item = entities.NotaFiscalItem(
                nota_id=db_nota.id,
                produto_id=item.produto_id,
                estoque_origem=item.estoque_origem,
                quantidade=item.quantidade,
                valor_unitario=item.valor_unitario,
                valor_total=item.valor_total,
                desconto_aplicado=item.desconto_aplicado,
                tipo_desconto=item.tipo_desconto,
                sincronizado=False
            )
            db.add(db_item)
        
        # Cria lançamento financeiro
        if not nota.a_prazo:  # Se não for a prazo, cria lançamento imediato
            financeiro = entities.Financeiro(
                tipo=TipoMovimentacao.entrada,
                categoria=CategoriaFinanceira.venda,
                valor=nota.valor_total,
                valor_desconto=nota.valor_desconto,
                descricao=f"Venda - Nota Fiscal #{db_nota.id}",
                data=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
                nota_fiscal_id=db_nota.id,
                cliente_id=nota.cliente_id,
                caixa_id=nota.caixa_id,
                sincronizado=False
            )
            db.add(financeiro)
        
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

def get_notas_fiscais(db: Session, skip: int = 0, limit: int = 100):
    notas = db.query(entities.NotaFiscal)\
              .order_by(entities.NotaFiscal.data_emissao.desc())\
              .offset(skip).limit(limit).all()
    for nota in notas:
        nota.itens = db.query(entities.NotaFiscalItem).filter(entities.NotaFiscalItem.nota_id == nota.id).all()
    return notas

def cancelar_nota_fiscal(db: Session, nota_id: int, motivo: str = "") -> bool:
    nota = get_nota_fiscal(db, nota_id)
    if not nota:
        raise ValueError("Nota fiscal não encontrada")
    
    if nota.status == StatusNota.cancelada:
        raise ValueError("Nota fiscal já está cancelada")
    
    # Reverte estoque dos itens
    for item in nota.itens:
        produto = get_produto(db, item.produto_id)
        if not produto:
            continue
        
        if item.estoque_origem == TipoEstoque.loja:
            produto.estoque_loja += item.quantidade
        elif item.estoque_origem == TipoEstoque.deposito:
            produto.estoque_deposito += item.quantidade
        elif item.estoque_origem == TipoEstoque.fabrica:
            produto.estoque_fabrica += item.quantidade
    
    # Atualiza status da nota
    nota.status = StatusNota.cancelada
    nota.observacao = f"Cancelada: {motivo}" if motivo else "Cancelada"
    nota.sincronizado = False
    
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao cancelar nota fiscal no banco de dados.")


def buscar_pagamentos_notas_fiscais(db: Session, ids_pagamentos: Union[int, List[int], Tuple[int], str]):
    """
    Busca informações detalhadas sobre pagamentos de notas fiscais por IDs.
    Inclui cálculo detalhado de descontos por produto, desconto total, endereço de entrega e informações do cliente.

    Args:
        db: Sessão do banco de dados
        ids_pagamentos: Pode ser um único ID (int), lista/tupla de IDs ou string com IDs separados por vírgula

    Returns:
        dict: {
            "count": número de notas encontradas,
            "data": lista de dicionários com informações completas,
            "success": booleano
        }
    """
    # Normalização da entrada
    if ids_pagamentos is None:
        return {"count": 0, "data": [], "success": True}

    if isinstance(ids_pagamentos, str):
        ids_pagamentos = [int(id.strip()) for id in ids_pagamentos.split(',') if id.strip().isdigit()]
    elif not isinstance(ids_pagamentos, (list, tuple)):
        ids_pagamentos = [ids_pagamentos]

    # Remove duplicatas mantendo a ordem
    seen = set()
    ids_unicos = [x for x in ids_pagamentos if not (x in seen or seen.add(x))]

    # Validação dos IDs
    try:
        ids_unicos = [int(id) for id in ids_unicos]
    except (ValueError, TypeError):
        raise ValueError("Todos os IDs devem ser valores numéricos")

    # Consulta otimizada ao banco de dados com JOIN para cliente
    pagamentos = db.query(PagamentoNotaFiscal)\
        .options(
            joinedload(PagamentoNotaFiscal.nota_fiscal)
            .joinedload(NotaFiscal.itens)
            .joinedload(NotaFiscalItem.produto),
            joinedload(PagamentoNotaFiscal.nota_fiscal)
            .joinedload(NotaFiscal.operador),
            joinedload(PagamentoNotaFiscal.nota_fiscal)
            .joinedload(NotaFiscal.pagamentos),
            joinedload(PagamentoNotaFiscal.nota_fiscal)
            .joinedload(NotaFiscal.entrega),
            joinedload(PagamentoNotaFiscal.nota_fiscal)
            .joinedload(NotaFiscal.cliente)  # Carrega o relacionamento com cliente
        )\
        .filter(PagamentoNotaFiscal.id.in_(ids_unicos))\
        .all()

    pagamentos_por_id = {p.id: p for p in pagamentos}
    resultados = []

    for id_solicitado in ids_pagamentos:
        id_solicitado = int(id_solicitado)
        if id_solicitado not in pagamentos_por_id:
            continue

        pagamento = pagamentos_por_id[id_solicitado]
        nota_fiscal = pagamento.nota_fiscal

        # Processamento das informações do cliente
        cliente_info = None
        if nota_fiscal.cliente:
            cliente_info = {
                'id': nota_fiscal.cliente.id,
                'nome': nota_fiscal.cliente.nome,
                'documento': nota_fiscal.cliente.documento,
                'telefone': nota_fiscal.cliente.telefone,
                'email': nota_fiscal.cliente.email,
                'endereco': nota_fiscal.cliente.endereco,
                'limite_credito': float(nota_fiscal.cliente.limite_credito) if nota_fiscal.cliente.limite_credito else None
            }

        # Cálculo dos valores totais
        valor_total_sem_desconto = sum(
            float(item.valor_unitario) * float(item.quantidade)
            for item in nota_fiscal.itens
        )
        desconto_total = valor_total_sem_desconto - float(nota_fiscal.valor_total)

        # Processamento dos produtos
        produtos = []
        for item in nota_fiscal.itens:
            valor_item_sem_desconto = float(item.valor_unitario) * float(item.quantidade)
            valor_item_com_desconto = float(item.valor_total)
            desconto_item = valor_item_sem_desconto - valor_item_com_desconto

            produtos.append({
                'id': item.produto.id,
                'nome': item.produto.nome,
                'codigo': item.produto.codigo,
                'quantidade': float(item.quantidade),
                'valor_unitario': float(item.valor_unitario),
                'valor_total_sem_desconto': valor_item_sem_desconto,
                'valor_total_com_desconto': valor_item_com_desconto,
                'desconto_aplicado': float(item.desconto_aplicado) if item.desconto_aplicado else None,
                'tipo_desconto': item.tipo_desconto.value if item.tipo_desconto else None,
                'valor_desconto': desconto_item,
                'percentual_desconto': round((desconto_item / valor_item_sem_desconto * 100), 2) if valor_item_sem_desconto > 0 else 0
            })

        # Formas de pagamento
        formas_pagamento = [{
            'id': pg.id,
            'forma_pagamento': pg.forma_pagamento.value,
            'valor': float(pg.valor),
            'data': pg.data.isoformat()
        } for pg in nota_fiscal.pagamentos]

        # Endereço de entrega (se existir)
        endereco_entrega = None
        if nota_fiscal.entrega:
            endereco_entrega = {
                'logradouro': nota_fiscal.entrega.logradouro,
                'numero': nota_fiscal.entrega.numero,
                'complemento': nota_fiscal.entrega.complemento,
                'bairro': nota_fiscal.entrega.bairro,
                'cidade': nota_fiscal.entrega.cidade,
                'estado': nota_fiscal.entrega.estado,
                'cep': nota_fiscal.entrega.cep,
                'instrucoes': nota_fiscal.entrega.instrucoes
            }

        # Resultado final para esta nota
        resultados.append({
            'pagamento_id': pagamento.id,
            'nota_fiscal_id': nota_fiscal.id,
            'data_emissao': nota_fiscal.data_emissao.isoformat(),
            'valor_total_nota': float(nota_fiscal.valor_total),
            'valor_total_sem_desconto': valor_total_sem_desconto,
            'desconto_total_calculado': desconto_total,
            'percentual_desconto_total': round((desconto_total / valor_total_sem_desconto * 100), 2) if valor_total_sem_desconto > 0 else 0,
            'valor_desconto_nota': float(nota_fiscal.valor_desconto) if nota_fiscal.valor_desconto else None,
            'operador': {
                'id': nota_fiscal.operador.id,
                'nome': nota_fiscal.operador.nome,
                'tipo': nota_fiscal.operador.tipo.value
            },
            'cliente': cliente_info,  # Incluído as informações do cliente
            'produtos': produtos,
            'formas_pagamento': formas_pagamento,
            'endereco_entrega': endereco_entrega,
            'pagamento_especifico': {
                'forma_pagamento': pagamento.forma_pagamento.value,
                'valor': float(pagamento.valor),
                'data': pagamento.data.isoformat()
            },
            'encontrado': True,
            'metadados': {
                'total_itens': len(nota_fiscal.itens),
                'total_formas_pagamento': len(nota_fiscal.pagamentos),
                'possui_entrega': endereco_entrega is not None,
                'possui_cliente': cliente_info is not None  # Novo metadado
            }
        })

    return {
        "count": len(resultados),
        "data": resultados,
        "success": True
    }
    
# ===== Contas a Receber =====
def create_conta_receber(db: Session, conta: schemas.ContaReceberCreate) -> entities.ContaReceber:
    if conta.valor_original <= 0:
        raise ValueError("Valor original deve ser maior que zero")
    
    if conta.valor_aberto <= 0:
        raise ValueError("Valor em aberto deve ser maior que zero")
    
    if conta.valor_aberto > conta.valor_original:
        raise ValueError("Valor em aberto não pode ser maior que valor original")
    
    cliente = get_cliente(db, conta.cliente_id)
    if not cliente:
        raise ValueError("Cliente não encontrado")
    
    if conta.nota_fiscal_id:
        nota = get_nota_fiscal(db, conta.nota_fiscal_id)
        if not nota:
            raise ValueError("Nota fiscal não encontrada")
    
    db_conta = entities.ContaReceber(
        cliente_id=conta.cliente_id,
        nota_fiscal_id=conta.nota_fiscal_id,
        descricao=conta.descricao,
        valor_original=conta.valor_original,
        valor_aberto=conta.valor_aberto,
        data_vencimento=conta.data_vencimento,
        data_emissao=conta.data_emissao or datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        status=conta.status,
        observacoes=conta.observacoes,
        sincronizado=False
    )
    
    db.add(db_conta)
    try:
        db.commit()
        db.refresh(db_conta)
        return db_conta
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao criar conta a receber no banco de dados.")

def get_conta_receber(db: Session, conta_id: int) -> Optional[entities.ContaReceber]:
    return db.query(entities.ContaReceber).filter(entities.ContaReceber.id == conta_id).first()

def get_contas_receber(db: Session, skip: int = 0, limit: int = 100) -> List[entities.ContaReceber]:
    return db.query(entities.ContaReceber)\
             .order_by(entities.ContaReceber.data_vencimento.asc())\
             .offset(skip).limit(limit).all()

def get_contas_receber_pendentes(db: Session) -> List[entities.ContaReceber]:
    return db.query(entities.ContaReceber)\
             .filter(entities.ContaReceber.status != StatusPagamento.quitado)\
             .order_by(entities.ContaReceber.data_vencimento.asc())\
             .all()

def update_conta_receber(db: Session, conta_id: int, conta_data: schemas.ContaReceberBase) -> Optional[entities.ContaReceber]:
    conta = get_conta_receber(db, conta_id)
    if not conta:
        return None
    
    update_data = conta_data.dict(exclude_unset=True)
    
    if "valor_original" in update_data and update_data["valor_original"] <= 0:
        raise ValueError("Valor original deve ser maior que zero")
    
    if "valor_aberto" in update_data:
        if update_data["valor_aberto"] <= 0:
            raise ValueError("Valor em aberto deve ser maior que zero")
        if update_data["valor_aberto"] > conta.valor_original:
            raise ValueError("Valor em aberto não pode ser maior que valor original")
    
    for field, value in update_data.items():
        setattr(conta, field, value)
    
    conta.sincronizado = False
    
    try:
        db.commit()
        db.refresh(conta)
        return conta
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao atualizar conta a receber no banco de dados.")

def delete_conta_receber(db: Session, conta_id: int) -> bool:
    conta = get_conta_receber(db, conta_id)
    if not conta:
        return False
    
    try:
        db.delete(conta)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao remover conta a receber no banco de dados.")

# ===== Pagamentos Contas a Receber =====
def registrar_pagamento_conta(db: Session, pagamento: schemas.PagamentoContaReceberCreate) -> entities.PagamentoContaReceber:
    if pagamento.valor_pago <= 0:
        raise ValueError("Valor do pagamento deve ser maior que zero")
    
    conta = get_conta_receber(db, pagamento.conta_id)
    if not conta:
        raise ValueError("Conta a receber não encontrada")
    
    if pagamento.valor_pago > conta.valor_aberto:
        raise ValueError("Valor do pagamento excede o valor em aberto")
    
    if pagamento.caixa_id:
        caixa = get_caixa_by_id(db, pagamento.caixa_id)
        if not caixa:
            raise ValueError("Caixa não encontrado")
    
    db_pagamento = entities.PagamentoContaReceber(
        conta_id=pagamento.conta_id,
        caixa_id=pagamento.caixa_id,
        valor_pago=pagamento.valor_pago,
        forma_pagamento=pagamento.forma_pagamento,
        observacoes=pagamento.observacoes,
        data_pagamento=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        sincronizado=False
    )
    db.add(db_pagamento)
    
    # Atualiza conta
    conta.valor_aberto -= pagamento.valor_pago
    conta.status = StatusPagamento.quitado if conta.valor_aberto == 0 else StatusPagamento.parcial
    conta.sincronizado = False
    
    # Cria lançamento financeiro
    financeiro = entities.Financeiro(
        tipo=TipoMovimentacao.entrada,
        categoria=CategoriaFinanceira.venda,
        valor=pagamento.valor_pago,
        descricao=f"Pagamento conta #{conta.id}",
        data=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        conta_receber_id=conta.id,
        cliente_id=conta.cliente_id,
        caixa_id=pagamento.caixa_id,
        sincronizado=False
    )
    db.add(financeiro)
    
    try:
        db.commit()
        db.refresh(db_pagamento)
        return db_pagamento
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Erro ao registrar pagamento no banco de dados.")

def get_pagamento_by_id(db: Session, pagamento_id: int) -> Optional[entities.PagamentoContaReceber]:
    return db.query(entities.PagamentoContaReceber).filter(entities.PagamentoContaReceber.id == pagamento_id).first()

def get_pagamentos_conta(db: Session, conta_id: int) -> List[entities.PagamentoContaReceber]:
    return db.query(entities.PagamentoContaReceber)\
             .filter(entities.PagamentoContaReceber.conta_id == conta_id)\
             .order_by(entities.PagamentoContaReceber.data_pagamento.asc())\
             .all()

# ===== Financeiro =====
def create_lancamento_financeiro(db: Session, lancamento: schemas.FinanceiroCreate) -> entities.Financeiro:
    if lancamento.valor <= 0:
        raise ValueError("Valor deve ser maior que zero.")
    
    if lancamento.tipo not in [t.value for t in TipoMovimentacao]:
        raise ValueError(f"Tipo de lançamento inválido. Deve ser um dos: {[t.value for t in TipoMovimentacao]}")
    
    if lancamento.categoria not in [c.value for c in CategoriaFinanceira]:
        raise ValueError(f"Categoria inválida. Deve ser um dos: {[c.value for c in CategoriaFinanceira]}")
    
    if lancamento.nota_fiscal_id:
        nota = get_nota_fiscal(db, lancamento.nota_fiscal_id)
        if not nota:
            raise ValueError("Nota fiscal não encontrada.")
    
    if lancamento.cliente_id:
        cliente = get_cliente(db, lancamento.cliente_id)
        if not cliente:
            raise ValueError("Cliente não encontrado.")
    
    if lancamento.caixa_id:
        caixa = get_caixa_by_id(db, lancamento.caixa_id)
        if not caixa:
            raise ValueError("Caixa não encontrado.")
    
    if lancamento.conta_receber_id:
        conta = get_conta_receber(db, lancamento.conta_receber_id)
        if not conta:
            raise ValueError("Conta a receber não encontrada.")
    
    db_lancamento = entities.Financeiro(
        tipo=lancamento.tipo,
        categoria=lancamento.categoria,
        valor=lancamento.valor,
        valor_desconto=lancamento.valor_desconto or Decimal('0.00'),
        descricao=lancamento.descricao,
        data=lancamento.data or datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
        nota_fiscal_id=lancamento.nota_fiscal_id,
        cliente_id=lancamento.cliente_id,
        caixa_id=lancamento.caixa_id,
        conta_receber_id=lancamento.conta_receber_id,
        sincronizado=False
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
    limit: Optional[int] = None,
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
    
    query = query.order_by(entities.Financeiro.data.desc()).offset(skip)
    
    if limit is not None:
        query = query.limit(limit)
        
    return query.all()

def listar_despesas_do_dia(db: Session, fuso: str = "America/Sao_Paulo"):
    """
    Retorna todas as despesas (tipo=saida, categoria=despesa) do dia atual.
    """
    agora = datetime.now(ZoneInfo(fuso))
    inicio_dia = datetime.combine(agora.date(), time.min).replace(tzinfo=ZoneInfo(fuso))
    fim_dia = datetime.combine(agora.date(), time.max).replace(tzinfo=ZoneInfo(fuso))

    despesas = db.query(entities.Financeiro).filter(
        entities.Financeiro.tipo == TipoMovimentacao.saida,
        entities.Financeiro.categoria == CategoriaFinanceira.despesa,
        entities.Financeiro.data >= inicio_dia,
        entities.Financeiro.data <= fim_dia
    ).all()

    return despesas

def update_lancamento_financeiro(
    db: Session, 
    lancamento_id: int, 
    lancamento_data: schemas.FinanceiroBase
) -> Optional[entities.Financeiro]:
    lancamento = get_lancamento_financeiro(db, lancamento_id)
    if not lancamento:
        return None
    
    if lancamento_data.valor and lancamento_data.valor <= 0:
        raise ValueError("Valor deve ser maior que zero.")
    
    if lancamento_data.tipo and lancamento_data.tipo not in [t.value for t in TipoMovimentacao]:
        raise ValueError(f"Tipo de lançamento inválido. Deve ser um dos: {[t.value for t in TipoMovimentacao]}")
    
    if lancamento_data.categoria and lancamento_data.categoria not in [c.value for c in CategoriaFinanceira]:
        raise ValueError(f"Categoria inválida. Deve ser um dos: {[c.value for c in CategoriaFinanceira]}")
    
    update_data = lancamento_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(lancamento, field, value)
    
    lancamento.sincronizado = False
    
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
        # Verificação dos campos obrigatórios básicos da venda
        if 'cliente_id' not in dados:
            raise ValueError('Campo obrigatório faltando: cliente_id')
        if 'forma_pagamento' not in dados:
            raise ValueError('Campo obrigatório faltando: forma_pagamento')
        if 'itens' not in dados or not isinstance(dados['itens'], list) or len(dados['itens']) == 0:
            raise ValueError('Lista de itens inválida ou vazia')

        # Processamento do endereço de entrega (com tratamento para campos nulos)
        entrega = None
        if dados.get("endereco_entrega"):
            entrega_data = dados["endereco_entrega"]
            
            # Cria o objeto de entrega apenas se algum campo foi preenchido
            if any(v for k, v in entrega_data.items() if v):
                entrega = entities.Entrega(
                    logradouro=entrega_data.get("logradouro") or "",
                    numero=entrega_data.get("numero") or "",
                    complemento=entrega_data.get("complemento") or "",
                    bairro=entrega_data.get("bairro") or "",
                    cidade=entrega_data.get("cidade") or "",
                    estado=entrega_data.get("estado") or "",
                    cep=entrega_data.get("cep") or "",
                    instrucoes=entrega_data.get("instrucoes") or "",
                    sincronizado=False,
                )
                db.add(entrega)
                db.flush()

        # Processamento dos itens da venda
        produtos_para_atualizar = {}
        valor_total = Decimal("0.00")
        valor_desconto_total = Decimal("0.00")

        for item in dados["itens"]:
            # Verificação dos campos obrigatórios dos itens
            required_fields = ['produto_id', 'quantidade', 'valor_unitario']
            for field in required_fields:
                if field not in item:
                    raise ValueError(f'Item da venda está faltando o campo: {field}')

            produto_id = item["produto_id"]
            quantidade = Decimal(str(item["quantidade"]))
            valor_unitario = Decimal(str(item["valor_unitario"]))
            valor_total_item = Decimal(str(item.get("valor_total", float(valor_unitario) * float(quantidade))))
            
            # Calcula desconto por item
            valor_sem_desconto = valor_unitario * quantidade
            desconto_item = valor_sem_desconto - valor_total_item
            
            produto = db.query(entities.Produto).filter(
                entities.Produto.id == produto_id
            ).with_for_update().one_or_none()

            if not produto:
                raise ValueError(f"Produto com ID {produto_id} não encontrado.")
            
            estoque_origem = item.get("estoque_origem", TipoEstoque.loja)

            produtos_para_atualizar[produto_id] = {
                "produto": produto,
                "quantidade": quantidade,
                "estoque_origem": estoque_origem,
                "desconto_aplicado": desconto_item
            }

            valor_total += valor_total_item
            valor_desconto_total += desconto_item

        valor_recebido = Decimal(str(dados.get("valor_recebido", 0)))
        troco = max(valor_recebido - valor_total, Decimal("0.00"))
        a_prazo = dados["forma_pagamento"] == "a_prazo"

        # Criação da nota fiscal
        nota = entities.NotaFiscal(
            cliente_id=dados["cliente_id"],
            operador_id=operador_id,
            caixa_id=caixa_id,
            entrega_id=entrega.id if entrega else None,
            valor_total=valor_total,
            valor_desconto=valor_desconto_total,
            tipo_desconto=TipoDesconto.fixo if valor_desconto_total > 0 else None,
            status=StatusNota.emitida,
            observacao=dados.get("observacao", ""),
            forma_pagamento=dados["forma_pagamento"],
            valor_recebido=valor_recebido,
            troco=troco,
            a_prazo=a_prazo,
            sincronizado=False,
            data_emissao=datetime.now(ZoneInfo("America/Sao_Paulo")),
        )
        db.add(nota)
        db.flush()

        # Processa itens e movimentações de estoque
        for item in dados["itens"]:
            produto_id = item["produto_id"]
            produto_info = produtos_para_atualizar[produto_id]
            
            # Atualiza estoque (agora permite valores negativos)
            if produto_info["estoque_origem"] == TipoEstoque.loja:
                produto_info["produto"].estoque_loja -= produto_info["quantidade"]
            elif produto_info["estoque_origem"] == TipoEstoque.deposito:
                produto_info["produto"].estoque_deposito -= produto_info["quantidade"]
            elif produto_info["estoque_origem"] == TipoEstoque.fabrica:
                produto_info["produto"].estoque_fabrica -= produto_info["quantidade"]

            # Cria item da nota
            nota_item = entities.NotaFiscalItem(
                nota_id=nota.id,
                produto_id=produto_id,
                estoque_origem=produto_info["estoque_origem"],
                quantidade=produto_info["quantidade"],
                valor_unitario=Decimal(str(item["valor_unitario"])),
                valor_total=Decimal(str(item.get("valor_total", float(item["valor_unitario"]) * float(produto_info["quantidade"])))),
                desconto_aplicado=produto_info["desconto_aplicado"],
                tipo_desconto=TipoDesconto.fixo if produto_info["desconto_aplicado"] > 0 else None,
                sincronizado=False,
            )
            db.add(nota_item)

            # Registra movimentação de estoque
            db.add(entities.MovimentacaoEstoque(
                produto_id=produto_id,
                usuario_id=operador_id,
                cliente_id=dados["cliente_id"],
                caixa_id=caixa_id,
                tipo=TipoMovimentacao.saida,
                estoque_origem=produto_info["estoque_origem"],
                quantidade=produto_info["quantidade"],
                valor_unitario=Decimal(str(item["valor_unitario"])),
                valor_recebido=valor_recebido,
                troco=troco,
                forma_pagamento=dados["forma_pagamento"],
                observacao=dados.get("observacao", ""),
                sincronizado=False,
                data=datetime.now(ZoneInfo("America/Sao_Paulo")),
            ))

        # Lançamento financeiro
        if not a_prazo:
            db.add(entities.Financeiro(
                tipo=TipoMovimentacao.entrada,
                categoria=CategoriaFinanceira.venda,
                valor=valor_total,
                valor_desconto=valor_desconto_total,
                descricao=f"Venda para cliente ID {dados['cliente_id']}",
                data=datetime.now(ZoneInfo("America/Sao_Paulo")),
                nota_fiscal_id=nota.id,
                cliente_id=dados["cliente_id"],
                caixa_id=caixa_id,
                sincronizado=False,
            ))
        else:
            db.add(entities.ContaReceber(
                cliente_id=dados["cliente_id"],
                nota_fiscal_id=nota.id,
                descricao=f"Venda a prazo - Nota #{nota.id}",
                valor_original=valor_total,
                valor_aberto=valor_total,
                data_vencimento=datetime.now(ZoneInfo("America/Sao_Paulo")) + timedelta(days=30),
                data_emissao=datetime.now(ZoneInfo("America/Sao_Paulo")),
                status=StatusPagamento.pendente,
                observacoes=dados.get("observacao", ""),
                sincronizado=False
            ))

        db.commit()
        return nota.id

    except Exception as e:
        db.rollback()
        raise

def estornar_venda(db, nota_fiscal_id, motivo_estorno, usuario_id):
    """
    Estorna uma venda vinculando ao caixa original da nota fiscal
    """
    try:
        # Busca a nota fiscal original
        nota_original = NotaFiscal.query.get(nota_fiscal_id)
        if not nota_original:
            return {'success': False, 'message': 'Nota fiscal não encontrada'}
        
        if nota_original.status == StatusNota.cancelada:
            return {'success': False, 'message': 'Esta nota já foi cancelada anteriormente'}
        
        # Usa o mesmo caixa da nota original em vez de buscar caixa aberto
        caixa_id = nota_original.caixa_id
        
        # Cria uma nova nota fiscal de estorno (com valores negativos)
        nota_estorno = NotaFiscal(
            cliente_id=nota_original.cliente_id,
            operador_id=usuario_id,
            caixa_id=caixa_id,  # Usa o mesmo caixa da nota original
            data_emissao=datetime.now(ZoneInfo('America/Sao_Paulo')),
            valor_total=-nota_original.valor_total,
            valor_desconto=-nota_original.valor_desconto if nota_original.valor_desconto else 0.00,
            tipo_desconto=nota_original.tipo_desconto,
            status=StatusNota.emitida,
            observacao=f"ESTORNO da nota #{nota_original.id}. Motivo: {motivo_estorno}",
            forma_pagamento=nota_original.forma_pagamento,
            a_prazo=nota_original.a_prazo,
            sincronizado=False
        )
        
        db.session.add(nota_estorno)
        db.session.flush()
        
        # Cria os itens de estorno (com quantidades negativas)
        for item in nota_original.itens:
            item_estorno = NotaFiscalItem(
                nota_id=nota_estorno.id,
                produto_id=item.produto_id,
                estoque_origem=item.estoque_origem,
                quantidade=-item.quantidade,
                valor_unitario=item.valor_unitario,
                valor_total=-item.valor_total,
                desconto_aplicado=-item.desconto_aplicado if item.desconto_aplicado else 0.00,
                tipo_desconto=item.tipo_desconto,
                sincronizado=False
            )
            db.session.add(item_estorno)
            
            # Cria movimentação de estoque reversa
            movimentacao = MovimentacaoEstoque(
                produto_id=item.produto_id,
                usuario_id=usuario_id,
                cliente_id=nota_original.cliente_id,
                caixa_id=caixa_id,  # Usa o mesmo caixa da nota original
                tipo=TipoMovimentacao.entrada,
                estoque_origem=item.estoque_origem,
                quantidade=item.quantidade,
                valor_unitario=item.valor_unitario,
                valor_recebido=0,
                forma_pagamento=None,
                observacao=f"Estorno nota #{nota_original.id}",
                data=datetime.now(ZoneInfo('America/Sao_Paulo')),
                sincronizado=False
            )
            db.session.add(movimentacao)
        
        # Atualiza status da nota original para cancelada
        nota_original.status = StatusNota.cancelada
        nota_original.observacao = f"Cancelada por estorno. Motivo: {motivo_estorno}"
        nota_original.sincronizado = False
        
        # Registra no financeiro
        financeiro_estorno = Financeiro(
            tipo=TipoMovimentacao.saida_estorno,
            categoria=CategoriaFinanceira.estorno,
            valor=-nota_original.valor_total,
            descricao=f"Estorno da nota #{nota_original.id}",
            caixa_id=caixa_id,  # Usa o mesmo caixa da nota original
            cliente_id=nota_original.cliente_id,
            nota_fiscal_id=nota_estorno.id,
            data=datetime.now(ZoneInfo('America/Sao_Paulo')),
            sincronizado=False
        )
        db.session.add(financeiro_estorno)
        
        # Cancela contas a receber associadas
        for conta in nota_original.contas_receber:
            if conta.status != StatusPagamento.quitado:
                conta.status = StatusPagamento.cancelado
                conta.observacoes = f"Cancelada devido ao estorno da nota #{nota_original.id}"
                conta.sincronizado = False
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Estorno realizado com sucesso',
            'nota_estorno_id': nota_estorno.id,
            'nota_original_id': nota_original.id
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erro ao estornar venda: {str(e)}'}

def obter_detalhes_vendas_dia(data=None, caixa_id=None, operador_id=None):
    """
    Obtém todos os detalhes das vendas do dia, incluindo totais de entradas/saídas, categorias e pagamentos
    
    Args:
        data (date, optional): Data para filtrar (default: dia atual)
        caixa_id (int, optional): ID do caixa para filtrar
        operador_id (int, optional): ID do operador para filtrar
    
    Returns:
        dict: Dicionário com os detalhes consolidados das vendas do dia
    """
    try:
        # Obtém as notas fiscais do dia
        notas = NotaFiscal.obter_vendas_do_dia(data, caixa_id, operador_id)
        
        # Inicializa estruturas para consolidação
        consolidado = {
            'total_vendas': 0.0,
            'total_descontos': 0.0,
            'total_entradas': 0.0,
            'total_saidas': 0.0,
            'por_forma_pagamento': {},
            'por_categoria': {
                'venda': 0.0,
                'abertura_caixa': 0.0,
                'fechamento_caixa': 0.0,
                'outro': 0.0
            },
            'vendas': [],
            'movimentacoes_financeiras': []
        }
        
        # Processa cada nota fiscal
        for nota in notas:
            # Adiciona aos totais
            consolidado['total_vendas'] += float(nota.valor_total)
            consolidado['total_descontos'] += float(nota.valor_desconto) if nota.valor_desconto else 0.0
            
            # Obtém os pagamentos da nota fiscal
            pagamentos = []
            total_pagamentos = 0.0
            for pagamento in nota.pagamentos:
                pagamentos.append({
                    'forma_pagamento': pagamento.forma_pagamento.value,
                    'valor': float(pagamento.valor),
                    'data': pagamento.data.isoformat()
                })
                total_pagamentos += float(pagamento.valor)
            
            # Forma de pagamento (para compatibilidade com versões antigas)
            forma_pagamento = nota.forma_pagamento.value if nota.forma_pagamento else 'nao_informado'
            if forma_pagamento not in consolidado['por_forma_pagamento']:
                consolidado['por_forma_pagamento'][forma_pagamento] = 0.0
            consolidado['por_forma_pagamento'][forma_pagamento] += float(nota.valor_total)
            
            # Adiciona detalhes da venda
            venda_info = {
                'id': nota.id,
                'data': nota.data_emissao.isoformat(),
                'cliente': nota.cliente.nome if nota.cliente else 'Consumidor',
                'operador': nota.operador.nome,
                'valor_total': float(nota.valor_total),
                'valor_desconto': float(nota.valor_desconto) if nota.valor_desconto else 0.0,
                'forma_pagamento': forma_pagamento,  # Mantido para compatibilidade
                'a_prazo': nota.a_prazo,
                'pagamentos': pagamentos,  # Novo campo com detalhes dos pagamentos
                'total_pagamentos': total_pagamentos,  # Soma dos valores pagos
                'diferenca_pagamentos': float(nota.valor_total) - total_pagamentos,  # Diferença entre total e pagamentos
                'itens': []
            }
            
            # Adiciona itens da venda
            for item in nota.itens:
                venda_info['itens'].append({
                    'produto': item.produto.nome,
                    'quantidade': float(item.quantidade),
                    'valor_unitario': float(item.valor_unitario),
                    'valor_total': float(item.valor_total),
                    'desconto': float(item.desconto_aplicado) if item.desconto_aplicado else 0.0
                })
            
            consolidado['vendas'].append(venda_info)
        
        # Obtém todas as movimentações financeiras do dia
        if data is None:
            data = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        
        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = datetime.combine(data, datetime.max.time())
        
        query = Financeiro.query.join(
            Caixa,
            Financeiro.caixa_id == Caixa.id
        ).filter(
            Financeiro.data >= inicio_dia,
            Financeiro.data <= fim_dia,
            Caixa.status == StatusCaixa.aberto
        )
        
        if caixa_id:
            query = query.filter(Financeiro.caixa_id == caixa_id)
        
        movimentacoes = query.all()
        
        # Processa as movimentações financeiras
        for mov in movimentacoes:
            valor = float(mov.valor)
            
            if mov.tipo == TipoMovimentacao.entrada:
                consolidado['total_entradas'] += valor
            else:
                consolidado['total_saidas'] += valor
            
            # Categorias financeiras
            categoria = mov.categoria.value if mov.categoria else 'outro'
            if categoria not in consolidado['por_categoria']:
                consolidado['por_categoria'][categoria] = 0.0
            consolidado['por_categoria'][categoria] += valor
            
            # Adiciona detalhes da movimentação
            consolidado['movimentacoes_financeiras'].append({
                'id': mov.id,
                'tipo': mov.tipo.value,
                'categoria': categoria,
                'valor': valor,
                'descricao': mov.descricao,
                'data': mov.data.isoformat(),
                'cliente': mov.cliente.nome if mov.cliente else None,
                'nota_fiscal_id': mov.nota_fiscal_id,
                'pagamento_id': mov.pagamento_id
            })
        
        return {
            'success': True,
            'data': consolidado,
            'total_geral': consolidado['total_entradas'] - consolidado['total_saidas']
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao obter detalhes das vendas: {str(e)}'
        }
        
'''
    Secção de descontos de produtos
'''
# CRIAR desconto (com lista de produto_ids)
def criar_desconto(session: Session, dados: dict) -> entities.Desconto:
    produto_ids = dados.pop('produto_ids', [])
    desconto = entities.Desconto(**dados)

    if produto_ids:
        produtos = session.query(entities.Produto).filter(entities.Produto.id.in_(produto_ids)).all()
        desconto.produtos.extend(produtos)

    session.add(desconto)
    session.commit()
    session.refresh(desconto)
    return desconto


# BUSCAR descontos por produto_id
def buscar_descontos_por_produto_id(session: Session, produto_id: int) -> list[entities.Desconto]:
    return (
        session.query(entities.Desconto)
        .join(entities.Desconto.produtos)
        .filter(entities.Produto.id == produto_id)
        .order_by(entities.Desconto.quantidade_minima.asc())
        .all()
    )

def buscar_desconto_by_id(session: Session, desconto_id: int) -> entities.Desconto | None:
    """
    Busca um desconto pelo ID.
    
    :param session: Sessão ativa do banco de dados.
    :param desconto_id: ID do desconto a ser buscado.
    :return: Objeto Desconto se encontrado, senão None.
    """
    return session.query(entities.Desconto).filter_by(id=desconto_id).first()

def buscar_todos_os_descontos(session: Session):
    """
    Retorna todos os descontos cadastrados no banco de dados.
    
    :param session: Sessão ativa do SQLAlchemy.
    :return: Lista de objetos Desconto.
    """
    return session.query(entities.Desconto).all()

# ATUALIZAR desconto (inclusive produtos vinculados)
def atualizar_desconto(session: Session, desconto_id: int, novos_dados: dict) -> entities.Desconto | None:
    desconto = session.query(entities.Desconto).get(desconto_id)
    if not desconto:
        return None

    produto_ids = novos_dados.pop('produto_ids', None)

    for chave, valor in novos_dados.items():
        setattr(desconto, chave, valor)

    if produto_ids is not None:
        produtos = session.query(entities.Produto).filter(entities.Produto.id.in_(produto_ids)).all()
        desconto.produtos = produtos 

    session.commit()
    session.refresh(desconto)
    return desconto


# DELETAR desconto
def deletar_desconto(session: Session, desconto_id: int) -> bool:
    desconto = session.query(entities.Desconto).get(desconto_id)
    if not desconto:
        return False
    session.delete(desconto)
    session.commit()
    return True


def obter_caixas_completo(session: Session) -> Dict[str, Any]:
    """
    Versão otimizada para retornar todos os caixas com informações completas.
    
    Principais otimizações aplicadas:
    1. Uso de selectinload para relacionamentos 1:N (evita N+1 queries)
    2. Processamento em lote dos dados
    3. Reutilização de objetos carregados
    4. Redução de conversões desnecessárias
    """
    try:
        # Carrega todos os caixas com relacionamentos otimizados
        caixas = (
            session.query(Caixa)
            .options(
                # Relacionamentos 1:1 com joinedload (mais eficiente)
                joinedload(Caixa.operador),
                joinedload(Caixa.administrador),
                
                # Relacionamentos 1:N com selectinload (evita N+1)
                selectinload(Caixa.financeiros),
                selectinload(Caixa.pagamentos),
                
                # Notas fiscais com todos os relacionamentos aninhados
                selectinload(Caixa.notas_fiscais).selectinload(NotaFiscal.cliente),
                selectinload(Caixa.notas_fiscais).selectinload(NotaFiscal.itens).joinedload(NotaFiscalItem.produto),
                selectinload(Caixa.notas_fiscais).selectinload(NotaFiscal.pagamentos),
                
                # Movimentações com produtos
                selectinload(Caixa.movimentacoes).joinedload(MovimentacaoEstoque.produto),
                selectinload(Caixa.movimentacoes).joinedload(MovimentacaoEstoque.cliente)
            )
            .order_by(Caixa.data_abertura.desc())
            .all()
        )

        # Processamento otimizado dos dados
        resultado = []
        
        for caixa in caixas:
            # Dados básicos do caixa (otimizado com verificações inline)
            caixa_data = {
                'id': caixa.id,
                'operador': _extrair_dados_usuario(caixa.operador),
                'administrador': _extrair_dados_usuario(caixa.administrador),
                'data_abertura': caixa.data_abertura.isoformat() if caixa.data_abertura else None,
                'data_fechamento': caixa.data_fechamento.isoformat() if caixa.data_fechamento else None,
                'data_analise': caixa.data_analise.isoformat() if caixa.data_analise else None,
                'valor_abertura': float(caixa.valor_abertura) if caixa.valor_abertura else 0.0,
                'valor_fechamento': float(caixa.valor_fechamento) if caixa.valor_fechamento else None,
                'valor_confirmado': float(caixa.valor_confirmado) if caixa.valor_confirmado else None,
                'status': caixa.status.value if caixa.status else None,
                'observacoes_operador': caixa.observacoes_operador,
                'observacoes_admin': caixa.observacoes_admin,
                'sincronizado': caixa.sincronizado,
                'financeiro': _processar_financeiros(caixa.financeiros),
                'vendas': _processar_notas_fiscais(caixa.notas_fiscais),
                'movimentacoes': _processar_movimentacoes(caixa.movimentacoes),
                'pagamentos': _processar_pagamentos_contas(caixa.pagamentos)
            }

            resultado.append(caixa_data)

        return {
            'success': True,
            'data': resultado,
            'count': len(resultado)
        }

    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar informações dos caixas'
        }


def _extrair_dados_usuario(usuario) -> Dict[str, Any]:
    """Função auxiliar para extrair dados do usuário de forma otimizada"""
    if not usuario:
        return None
    
    return {
        'id': usuario.id,
        'nome': usuario.nome,
        'tipo': usuario.tipo.value if usuario.tipo else None
    }


def _processar_financeiros(financeiros) -> List[Dict[str, Any]]:
    """Processa lista de financeiros de forma otimizada"""
    if not financeiros:
        return []
    
    return [
        {
            'id': f.id,
            'tipo': f.tipo.value if f.tipo else None,
            'categoria': f.categoria.value if f.categoria else None,
            'valor': float(f.valor) if f.valor else 0.0,
            'valor_desconto': float(f.valor_desconto) if f.valor_desconto else None,
            'descricao': f.descricao,
            'data': f.data.isoformat() if f.data else None,
            'nota_fiscal_id': f.nota_fiscal_id,
            'cliente_id': f.cliente_id,
            'conta_receber_id': f.conta_receber_id
        }
        for f in financeiros
    ]


def _processar_notas_fiscais(notas_fiscais) -> List[Dict[str, Any]]:
    """Processa lista de notas fiscais de forma otimizada"""
    if not notas_fiscais:
        return []
    
    resultado = []
    
    for nota in notas_fiscais:
        nota_data = {
            'id': nota.id,
            'data_emissao': nota.data_emissao.isoformat() if nota.data_emissao else None,
            'valor_total': float(nota.valor_total) if nota.valor_total else 0.0,
            'valor_desconto': float(nota.valor_desconto) if nota.valor_desconto else 0.0,
            'status': nota.status.value if nota.status else None,
            'cliente': _extrair_dados_cliente(nota.cliente),
            'itens': _processar_itens_nota(nota.itens),
            'pagamentos': _processar_pagamentos_nota(nota.pagamentos)
        }
        resultado.append(nota_data)
    
    return resultado


def _extrair_dados_cliente(cliente) -> Dict[str, Any]:
    """Função auxiliar para extrair dados do cliente"""
    if not cliente:
        return None
    
    return {
        'id': cliente.id,
        'nome': cliente.nome
    }


def _processar_itens_nota(itens) -> List[Dict[str, Any]]:
    """Processa itens da nota fiscal de forma otimizada"""
    if not itens:
        return []
    
    return [
        {
            'produto': {
                'id': item.produto.id if item.produto else None,
                'nome': item.produto.nome if item.produto else None,
                'codigo': item.produto.codigo if item.produto else None,
                'unidade': item.produto.unidade.value if item.produto and item.produto.unidade else None
            },
            'quantidade': float(item.quantidade) if item.quantidade else 0.0,
            'valor_unitario': float(item.valor_unitario) if item.valor_unitario else 0.0,
            'valor_total': float(item.valor_total) if item.valor_total else 0.0,
            'desconto_aplicado': float(item.desconto_aplicado) if item.desconto_aplicado else None,
            'tipo_desconto': item.tipo_desconto.value if item.tipo_desconto else None
        }
        for item in itens
    ]


def _processar_pagamentos_nota(pagamentos) -> List[Dict[str, Any]]:
    """Processa pagamentos da nota fiscal"""
    if not pagamentos:
        return []
    
    return [
        {
            'forma_pagamento': p.forma_pagamento.value if p.forma_pagamento else None,
            'valor': float(p.valor) if p.valor else 0.0,
            'data': p.data.isoformat() if p.data else None
        }
        for p in pagamentos
    ]


def _processar_movimentacoes(movimentacoes) -> List[Dict[str, Any]]:
    """Processa movimentações de estoque de forma otimizada"""
    if not movimentacoes:
        return []
    
    return [
        {
            'id': mov.id,
            'tipo': mov.tipo.value if mov.tipo else None,
            'produto': {
                'id': mov.produto.id if mov.produto else None,
                'nome': mov.produto.nome if mov.produto else None,
                'codigo': mov.produto.codigo if mov.produto else None
            },
            'quantidade': float(mov.quantidade) if mov.quantidade else 0.0,
            'valor_unitario': float(mov.valor_unitario) if mov.valor_unitario else 0.0,
            'valor_total': float(mov.valor_unitario) * float(mov.quantidade) if mov.valor_unitario and mov.quantidade else 0.0,
            'forma_pagamento': mov.forma_pagamento.value if mov.forma_pagamento else None,
            'data': mov.data.isoformat() if mov.data else None,
            'cliente': _extrair_dados_cliente(mov.cliente)
        }
        for mov in movimentacoes
    ]


def _processar_pagamentos_contas(pagamentos) -> List[Dict[str, Any]]:
    """Processa pagamentos de contas a receber"""
    if not pagamentos:
        return []
    
    return [
        {
            'id': p.id,
            'conta_receber_id': p.conta_id,
            'valor_pago': float(p.valor_pago) if p.valor_pago else 0.0,
            'forma_pagamento': p.forma_pagamento.value if p.forma_pagamento else None,
            'data_pagamento': p.data_pagamento.isoformat() if p.data_pagamento else None,
            'observacoes': p.observacoes
        }
        for p in pagamentos
    ]


# Versão alternativa com paginação para grandes volumes de dados
def obter_caixas_completo_paginado(session: Session, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """
    Versão paginada para quando há muitos registros de caixa.
    
    Args:
        session: Sessão do SQLAlchemy
        page: Página atual (inicia em 1)
        per_page: Registros por página
    """
    try:
        # Query com paginação
        query = (
            session.query(Caixa)
            .options(
                joinedload(Caixa.operador),
                joinedload(Caixa.administrador),
                selectinload(Caixa.financeiros),
                selectinload(Caixa.pagamentos),
                selectinload(Caixa.notas_fiscais).selectinload(NotaFiscal.cliente),
                selectinload(Caixa.notas_fiscais).selectinload(NotaFiscal.itens).joinedload(NotaFiscalItem.produto),
                selectinload(Caixa.notas_fiscais).selectinload(NotaFiscal.pagamentos),
                selectinload(Caixa.movimentacoes).joinedload(MovimentacaoEstoque.produto),
                selectinload(Caixa.movimentacoes).joinedload(MovimentacaoEstoque.cliente)
            )
            .order_by(Caixa.data_abertura.desc())
        )
        
        # Aplicar paginação
        total = query.count()
        caixas = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Processar dados (mesmo código da função principal)
        resultado = []
        for caixa in caixas:
            caixa_data = {
                'id': caixa.id,
                'operador': _extrair_dados_usuario(caixa.operador),
                'administrador': _extrair_dados_usuario(caixa.administrador),
                'data_abertura': caixa.data_abertura.isoformat() if caixa.data_abertura else None,
                'data_fechamento': caixa.data_fechamento.isoformat() if caixa.data_fechamento else None,
                'data_analise': caixa.data_analise.isoformat() if caixa.data_analise else None,
                'valor_abertura': float(caixa.valor_abertura) if caixa.valor_abertura else 0.0,
                'valor_fechamento': float(caixa.valor_fechamento) if caixa.valor_fechamento else None,
                'valor_confirmado': float(caixa.valor_confirmado) if caixa.valor_confirmado else None,
                'status': caixa.status.value if caixa.status else None,
                'observacoes_operador': caixa.observacoes_operador,
                'observacoes_admin': caixa.observacoes_admin,
                'sincronizado': caixa.sincronizado,
                'financeiro': _processar_financeiros(caixa.financeiros),
                'vendas': _processar_notas_fiscais(caixa.notas_fiscais),
                'movimentacoes': _processar_movimentacoes(caixa.movimentacoes),
                'pagamentos': _processar_pagamentos_contas(caixa.pagamentos)
            }
            resultado.append(caixa_data)
        
        return {
            'success': True,
            'data': resultado,
            'count': len(resultado),
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
        
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar informações dos caixas'
        }

def atualizar_caixa(session: Session, caixa_id: int, dados_atualizacao: dict):
    """
    Atualiza um caixa existente usando uma sessão explícita
    
    Args:
        session (Session): Sessão do SQLAlchemy
        caixa_id (int): ID do caixa a ser atualizado
        dados_atualizacao (dict): Dicionário com os campos a serem atualizados
        
    Returns:
        tuple: (Caixa atualizado, mensagem de sucesso/erro)
    """
    try:
        # Busca o caixa no banco de dados usando a sessão fornecida
        caixa = session.get(Caixa, caixa_id)
        if not caixa:
            return None, "Caixa não encontrado"
        
        # Verifica se o caixa está aberto
        if caixa.status != StatusCaixa.aberto:
            return None, "Só é possível atualizar caixas com status 'aberto'"
        
        # Campos permitidos para atualização
        campos_permitidos = {
            'valor_abertura', 
            'observacoes_operador'
        }
        
        # Atualiza apenas os campos permitidos
        for campo, valor in dados_atualizacao.items():
            if campo in campos_permitidos:
                setattr(caixa, campo, valor)
        
        # Marca como não sincronizado
        caixa.sincronizado = False
        caixa.atualizado_em = datetime.now()
        
        # Não faz commit aqui - deixa para o chamador controlar a transação
        return caixa, "Caixa atualizado com sucesso"
        
    except Exception as e:
        # Faz rollback explícito em caso de erro
        session.rollback()
        return None, f"Erro ao atualizar caixa: {str(e)}"