from app import create_app, db  # ou de onde você importa seu app e o db
from app.services.crud import buscar_descontos_por_produto_id

app = create_app()  # ou como você cria seu app Flask

with app.app_context():
    resultado = buscar_descontos_por_produto_id(db.session, 25)
    print(f"Iniciando testes para buscar descontos por produto_id...\n\n{resultado}\n")
