from flask import json
from app.database import SessionLocal
from app.models.entities import Produto

def buscar_detalhes_produto(produto_id):
    db = SessionLocal()
    try:
        produto = db.get(Produto, produto_id)

        if not produto:
            return None

        return {
            'id': produto.id,
            'nome': produto.nome,
            'codigo': produto.codigo,
            'preco_unitario': round(float(produto.valor_unitario), 2),
            'estoque_atual': round(float(produto.estoque_loja), 2),
            'created_at': produto.criado_em.isoformat() if produto.criado_em else None,
            'updated_at': produto.atualizado_em.isoformat() if produto.atualizado_em else None,
            'ativo': produto.ativo,
            'descontos': [
                {
                    'id': d.id,
                    'identificador': d.identificador,
                    'quantidade_minima': round(d.quantidade_minima, 2),
                    'quantidade_maxima': round(d.quantidade_maxima, 2),
                    'valor_desconto': round(float(d.valor), 2)
                }
                for d in produto.descontos
            ]
        }
    finally:
        db.close()


print(json.dumps(buscar_detalhes_produto(8), indent=2))