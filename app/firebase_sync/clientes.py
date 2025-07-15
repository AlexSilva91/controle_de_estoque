from app.firebase.config_firebase import clientes_ref
from app.models import entities

def sincronizar_clientes(db):
    clientes = db.query(entities.Cliente).filter(entities.Cliente.sincronizado == False).all()
    for c in clientes:
        data = {
            "id": c.id,
            "nome": c.nome,
            "documento": c.documento,
            "telefone": c.telefone,
            "email": c.email,
            "endereco": c.endereco,
            "ativo": c.ativo,
            "criado_em": c.criado_em.isoformat() if c.criado_em else None,
            "atualizado_em": c.atualizado_em.isoformat() if c.atualizado_em else None,
        }
        clientes_ref.document(str(c.id)).set(data)
        c.sincronizado = True
        db.commit()
