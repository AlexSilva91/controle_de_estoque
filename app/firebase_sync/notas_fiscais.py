from app.firebase.config_firebase import notas_fiscais_ref, itens_nota_ref
from app.models import entities

def sincronizar_notas_fiscais(db):
    notas = db.query(entities.NotaFiscal).filter(entities.NotaFiscal.sincronizado == False).all()
    for n in notas:
        data = {
            "id": n.id,
            "cliente_id": n.cliente_id,
            "operador_id": n.operador_id,
            "caixa_id": n.caixa_id,
            "data_emissao": n.data_emissao.isoformat() if n.data_emissao else None,
            "valor_total": float(n.valor_total),
            "status": n.status.value if n.status else None,
            "chave_acesso": n.chave_acesso,
            "observacao": n.observacao,
            "forma_pagamento": n.forma_pagamento.value if n.forma_pagamento else None,
            "valor_recebido": float(n.valor_recebido) if n.valor_recebido else None,
            "troco": float(n.troco) if n.troco else None,
        }
        notas_fiscais_ref.document(str(n.id)).set(data)

        # Sincroniza itens da nota fiscal
        for item in n.itens:
            item_data = {
                "id": item.id,
                "nota_id": item.nota_id,
                "produto_id": item.produto_id,
                "quantidade": float(item.quantidade),
                "valor_unitario": float(item.valor_unitario),
                "valor_total": float(item.valor_total),
            }
            itens_nota_ref.document(str(item.id)).set(item_data)

        n.sincronizado = True
        db.commit()
