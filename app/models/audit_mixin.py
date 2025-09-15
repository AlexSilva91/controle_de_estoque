from sqlalchemy.orm.attributes import get_history

class AuditMixin:
    @staticmethod
    def get_changes(instance):
        """Retorna dict com campos alterados (antes/depois)."""
        changes = {}
        for attr in instance.__mapper__.columns:
            hist = get_history(instance, attr.key)
            if not hist.has_changes():
                continue
            old_value = hist.deleted[0] if hist.deleted else None
            new_value = hist.added[0] if hist.added else None
            if old_value != new_value:
                changes[attr.key] = {"antes": str(old_value), "depois": str(new_value)}
        return changes
