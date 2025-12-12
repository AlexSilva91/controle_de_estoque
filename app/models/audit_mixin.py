from sqlalchemy.orm.attributes import get_history
from datetime import datetime, date
from decimal import Decimal
import enum

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

def deve_auditar_campo(tabela_nome, campo_nome):
    from .audit_events import AUDIT_CONFIG
    
    if tabela_nome in AUDIT_CONFIG['tabelas_ignoradas']:
        return False
        
    if not tabela_nome in AUDIT_CONFIG['tabelas_auditadas']:
        return False
    
    if campo_nome in AUDIT_CONFIG['campos_ignorados_globais']:
        return False
    
    campos_auditados = AUDIT_CONFIG['tabelas_auditadas'].get(tabela_nome, [])
    return campo_nome in campos_auditados

class AuditMixin:
    @staticmethod
    def get_changes(instance):
        changes = {}
        tabela_nome = instance.__tablename__
        
        for attr in instance.__mapper__.columns:
            campo_nome = attr.key
            
            if not deve_auditar_campo(tabela_nome, campo_nome):
                continue
                
            hist = get_history(instance, campo_nome)
            if not hist.has_changes():
                continue
                
            old_value = hist.deleted[0] if hist.deleted else None
            new_value = hist.added[0] if hist.added else None
            
            if old_value != new_value:
                old_value_str = formatar_valor_para_json(old_value)
                new_value_str = formatar_valor_para_json(new_value)
                changes[campo_nome] = {"antes": old_value_str, "depois": new_value_str}
        return changes