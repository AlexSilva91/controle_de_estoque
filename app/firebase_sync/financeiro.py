from app.firebase.config_firebase import financeiro_ref
from app.models import entities

def sincronizar_financeiro(db):
    financeiros = db.query(entities.Financeiro).filter(entities.Financeiro.sincronizado == False).all()
    for f in financeiros:
        data = {
            "id": f.id,
            "tipo": f.tipo.value if f.tipo else None,
            "categoria": f.categoria.value if f.categoria else None,
            "valor": float(f.valor),
            "descricao": f.descricao,
            "data": f.data.isoformat() if f.data else None,
            "nota_fiscal_id": f.nota_fiscal_id,
            "cliente_id": f.cliente_id,
            "caixa_id": f.caixa_id,
        }
        financeiro_ref.document(str(f.id)).set(data)
        f.sincronizado = True
        db.commit()
