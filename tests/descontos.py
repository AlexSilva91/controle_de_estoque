from app.database import SessionLocal
from app.models.entities import Produto

def buscar_descontos_por_produto_id(produto_id):
    db = SessionLocal()
    try:
        produto = db.get(Produto, produto_id)
        if not produto:
            return None
        return produto.descontos
    finally:
        db.close()

print(f'Descontos: {buscar_descontos_por_produto_id(31)}')
