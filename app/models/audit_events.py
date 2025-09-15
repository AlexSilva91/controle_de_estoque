# app/models/audit_events.py

from sqlalchemy import event
from flask_login import current_user
import json
from datetime import datetime
from . import db
from .entities import AuditLog, Base
from .audit_mixin import AuditMixin

def log_update(mapper, connection, target):
    changes = AuditMixin.get_changes(target)
    if changes:
        # Use datetime.now() explicitamente para criado_em
        connection.execute(
            AuditLog.__table__.insert(),
            {
                'tabela': target.__tablename__,
                'registro_id': target.id,
                'usuario_id': getattr(current_user, "id", None),
                'acao': 'update',
                'antes': json.dumps({c: v["antes"] for c,v in changes.items()}, ensure_ascii=False),
                'depois': json.dumps({c: v["depois"] for c,v in changes.items()}, ensure_ascii=False),
                'criado_em': datetime.now()  # Adicione esta linha
            }
        )

def log_insert(mapper, connection, target):
    # Use datetime.now() explicitamente para criado_em
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'tabela': target.__tablename__,
            'registro_id': target.id,
            'usuario_id': getattr(current_user, "id", None),
            'acao': 'insert',
            'depois': json.dumps({c.name: str(getattr(target, c.name)) for c in target.__table__.columns}, ensure_ascii=False),
            'criado_em': datetime.now()  # Adicione esta linha
        }
    )

def log_delete(mapper, connection, target):
    # Use datetime.now() explicitamente para criado_em
    connection.execute(
        AuditLog.__table__.insert(),
        {
            'tabela': target.__tablename__,
            'registro_id': target.id,
            'usuario_id': getattr(current_user, "id", None),
            'acao': 'delete',
            'antes': json.dumps({c.name: str(getattr(target, c.name)) for c in target.__table__.columns}, ensure_ascii=False),
            'criado_em': datetime.now()  # Adicione esta linha
        }
    )

# Registra os eventos globalmente
event.listen(Base, "after_update", log_update, propagate=True)
event.listen(Base, "after_insert", log_insert, propagate=True)
event.listen(Base, "after_delete", log_delete, propagate=True)