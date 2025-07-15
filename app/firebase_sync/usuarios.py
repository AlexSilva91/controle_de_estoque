from app.firebase.config_firebase import firestore_db, usuarios_ref
from app.models import entities

def sincronizar_usuarios(db):
    usuarios = db.query(entities.Usuario).filter(entities.Usuario.sincronizado == False).all()
    for u in usuarios:
        data = {
            "id": u.id,
            "nome": u.nome,
            "cpf": u.cpf,
            "tipo": u.tipo.value if u.tipo else None,
            "criado_em": u.criado_em.isoformat() if u.criado_em else None,
            "status": u.status,
            "ultimo_acesso": u.ultimo_acesso.isoformat() if u.ultimo_acesso else None,
            "observacoes": u.observacoes,
        }
        usuarios_ref.document(str(u.id)).set(data)
        u.sincronizado = True
        db.commit()
