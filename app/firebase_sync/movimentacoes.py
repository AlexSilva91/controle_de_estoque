from app.firebase.config_firebase import movimentacoes_ref
from app.models import entities

def sincronizar_movimentacoes(db):
    movimentacoes = db.query(entities.MovimentacaoEstoque).filter(entities.MovimentacaoEstoque.sincronizado == False).all()
    for m in movimentacoes:
        data = {
            "id": m.id,
            "produto_id": m.produto_id,
            "usuario_id": m.usuario_id,
            "cliente_id": m.cliente_id,
            "caixa_id": m.caixa_id,
            "tipo": m.tipo.value if m.tipo else None,
            "quantidade": float(m.quantidade),
            "valor_unitario": float(m.valor_unitario),
            "valor_recebido": float(m.valor_recebido) if m.valor_recebido else None,
            "troco": float(m.troco) if m.troco else None,
            "forma_pagamento": m.forma_pagamento.value if m.forma_pagamento else None,
            "observacao": m.observacao,
            "data": m.data.isoformat() if m.data else None,
        }
        movimentacoes_ref.document(str(m.id)).set(data)
        m.sincronizado = True
        db.commit()
