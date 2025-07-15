from app.firebase.config_firebase import firestore_db, clientes_ref
from app.firebase.config_firebase import firestore_db, caixas_ref
from app.models import entities

def sincronizar_caixas(db):
    caixas = db.query(entities.Caixa).filter(entities.Caixa.sincronizado == False).all()
    for cx in caixas:
        data = {
            "id": cx.id,
            "operador_id": cx.operador_id,
            "data_abertura": cx.data_abertura.isoformat() if cx.data_abertura else None,
            "data_fechamento": cx.data_fechamento.isoformat() if cx.data_fechamento else None,
            "valor_abertura": float(cx.valor_abertura),
            "valor_fechamento": float(cx.valor_fechamento) if cx.valor_fechamento else None,
            "status": cx.status.value if cx.status else None,
            "observacoes": cx.observacoes,
        }
        caixas_ref.document(str(cx.id)).set(data)
        cx.sincronizado = True
        db.commit()
