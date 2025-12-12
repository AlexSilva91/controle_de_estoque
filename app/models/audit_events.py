from sqlalchemy import event, inspect
from sqlalchemy.orm.attributes import get_history
from flask_login import current_user
import json
from datetime import datetime, date
from decimal import Decimal
import enum
from . import db
from .entities import AuditLog, Base

AUDIT_CONFIG = {
    'tabelas_auditadas': {
        'usuarios': ['nome', 'cpf', 'tipo', 'status', 'observacoes', 'ultimo_acesso'],
        'produtos': ['nome', 'valor_unitario', 'estoque_loja', 'estoque_deposito', 
                    'estoque_fabrica', 'ativo', 'valor_unitario_compra'],
        'clientes': ['nome', 'documento', 'telefone', 'email', 'endereco', 'ativo', 'limite_credito'],
        'caixas': ['status', 'valor_abertura', 'valor_fechamento', 'valor_confirmado',
                  'observacoes_operador', 'observacoes_admin', 'administrador_id'],
        'contas_receber': ['valor_aberto', 'status', 'data_pagamento', 'observacoes'],
        'financeiro': ['valor', 'categoria', 'descricao', 'tipo', 'nota_fiscal_id'],
        'movimentacoes_estoque': ['quantidade', 'valor_unitario', 'tipo', 'forma_pagamento',
                                 'valor_recebido', 'cliente_id'],
        'notas_fiscais': ['valor_total', 'status', 'forma_pagamento', 'valor_recebido', 
                         'cliente_id', 'valor_desconto'],
        'descontos': ['identificador', 'tipo', 'valor', 'ativo', 'valido_ate',
                     'quantidade_minima', 'quantidade_maxima']
    },
    
    'campos_ignorados_globais': [
        'atualizado_em',
        'criado_em',
        'sincronizado',
        'senha_hash',
        'id'
    ],
    
    'acoes_auditadas': ['insert', 'update', 'delete'],
    
    'tabelas_ignoradas': [
        'audit_logs',  
        'configuracoes',
        'produto_desconto_association'  
    ]
}

def deve_auditar_tabela(tabela_nome):
    if tabela_nome in AUDIT_CONFIG['tabelas_ignoradas']:
        return False
    return tabela_nome in AUDIT_CONFIG['tabelas_auditadas']

def deve_auditar_campo(tabela_nome, campo_nome):
    if not deve_auditar_tabela(tabela_nome):
        return False
    
    if campo_nome in AUDIT_CONFIG['campos_ignorados_globais']:
        return False
    
    campos_auditados = AUDIT_CONFIG['tabelas_auditadas'].get(tabela_nome, [])
    return campo_nome in campos_auditados

def formatar_valor_para_json(valor):
    if valor is None:
        return None
    elif isinstance(valor, (datetime, date)):
        return valor.isoformat()
    elif isinstance(valor, Decimal):
        return float(valor)
    elif isinstance(valor, enum.Enum):
        return valor.value
    elif isinstance(valor, (int, float, bool)):
        return valor
    else:
        return str(valor)

def get_campos_auditaveis_para_insert(instance):
    tabela_nome = instance.__tablename__
    if not deve_auditar_tabela(tabela_nome):
        return {}
    
    campos_auditados = {}
    
    insp = inspect(instance)
    
    for atributo in insp.mapper.column_attrs:
        campo_nome = atributo.key
        
        if not deve_auditar_campo(tabela_nome, campo_nome):
            continue
            
        valor = getattr(instance, campo_nome, None)
        if valor is not None:
            campos_auditados[campo_nome] = formatar_valor_para_json(valor)
    
    return campos_auditados

def get_campos_alterados_para_update(instance):
    tabela_nome = instance.__tablename__
    if not deve_auditar_tabela(tabela_nome):
        return {}
    
    alteracoes = {}
    
    for coluna in instance.__mapper__.columns:
        campo_nome = coluna.key
        
        if not deve_auditar_campo(tabela_nome, campo_nome):
            continue
            
        hist = get_history(instance, campo_nome)
        if not hist.has_changes():
            continue
            
        valor_antes = hist.deleted[0] if hist.deleted else None
        valor_depois = hist.added[0] if hist.added else None
        
        if valor_antes != valor_depois:
            alteracoes[campo_nome] = {
                "antes": formatar_valor_para_json(valor_antes),
                "depois": formatar_valor_para_json(valor_depois)
            }
    
    return alteracoes

def log_update(mapper, connection, target):
    if not deve_auditar_tabela(target.__tablename__) or 'update' not in AUDIT_CONFIG['acoes_auditadas']:
        return
    
    alteracoes = get_campos_alterados_para_update(target)
    if not alteracoes:
        return
    
    antes_json = {campo: valores["antes"] for campo, valores in alteracoes.items()}
    depois_json = {campo: valores["depois"] for campo, valores in alteracoes.items()}
    
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'tabela': target.__tablename__,
            'registro_id': target.id,
            'usuario_id': getattr(current_user, "id", None),
            'acao': 'update',
            'antes': json.dumps(antes_json, ensure_ascii=False) if antes_json else None,
            'depois': json.dumps(depois_json, ensure_ascii=False) if depois_json else None,
            'criado_em': datetime.now()
        }
    )

def log_insert(mapper, connection, target):
    if not deve_auditar_tabela(target.__tablename__) or 'insert' not in AUDIT_CONFIG['acoes_auditadas']:
        return
    
    campos_auditaveis = get_campos_auditaveis_para_insert(target)
    if not campos_auditaveis:
        return
    
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'tabela': target.__tablename__,
            'registro_id': target.id,
            'usuario_id': getattr(current_user, "id", None),
            'acao': 'insert',
            'depois': json.dumps(campos_auditaveis, ensure_ascii=False),
            'criado_em': datetime.now()
        }
    )

def log_delete(mapper, connection, target):
    if not deve_auditar_tabela(target.__tablename__) or 'delete' not in AUDIT_CONFIG['acoes_auditadas']:
        return
    
    campos_auditaveis = get_campos_auditaveis_para_insert(target)
    if not campos_auditaveis:
        return
    
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'tabela': target.__tablename__,
            'registro_id': target.id,
            'usuario_id': getattr(current_user, "id", None),
            'acao': 'delete',
            'antes': json.dumps(campos_auditaveis, ensure_ascii=False),
            'criado_em': datetime.now()
        }
    )

def setup_audit_events():
    event.listen(Base, "after_update", log_update, propagate=True)
    event.listen(Base, "after_insert", log_insert, propagate=True)
    event.listen(Base, "after_delete", log_delete, propagate=True)