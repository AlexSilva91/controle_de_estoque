from app.firebase.config_firebase import firestore_db, produtos_ref
from app.models import entities

def sincronizar_produtos(db):
    produtos = db.query(entities.Produto).filter(entities.Produto.sincronizado == False).all()
    for p in produtos:
        data = {
            "id": p.id,
            "codigo": p.codigo,
            "nome": p.nome,
            "tipo": p.tipo,
            "marca": p.marca,
            "unidade": p.unidade.value if p.unidade else None,
            "valor_unitario": float(p.valor_unitario),
            "estoque_quantidade": float(p.estoque_quantidade),
            "ativo": p.ativo,
            "criado_em": p.criado_em.isoformat() if p.criado_em else None,
            "atualizado_em": p.atualizado_em.isoformat() if p.atualizado_em else None,
        }
        produtos_ref.document(str(p.id)).set(data)
        p.sincronizado = True
        db.commit()
