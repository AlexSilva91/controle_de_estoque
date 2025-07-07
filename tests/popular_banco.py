from app import create_app
from app.models import db
from app.models.entities import Usuario, TipoUsuario, Cliente, Produto, UnidadeMedida
from passlib.context import CryptContext

app = create_app()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

with app.app_context():
    # Cria as tabelas se não existirem
    db.create_all()

    # --- USUÁRIOS ---
    usuarios = [
        {"nome": "Alex Alves", "cpf": "13166456491", "senha": "842695", "tipo": TipoUsuario.operador},
        {"nome": "Alex Alves", "cpf": "13166456490", "senha": "842695", "tipo": TipoUsuario.admin},
    ]

    for u in usuarios:
        if not Usuario.query.filter_by(cpf=u["cpf"]).first():
            senha_hash = pwd_context.hash(u["senha"])
            novo_usuario = Usuario(
                nome=u["nome"],
                cpf=u["cpf"],
                senha_hash=senha_hash,
                tipo=u["tipo"]
            )
            db.session.add(novo_usuario)
        else:
            print(f"Usuário com CPF {u['cpf']} já existe, pulando.")

    # --- CLIENTES ---
    clientes = [
        {"nome": "Cliente 1", "documento": "12345678901", "telefone": "11999999991", "email": "cli1@example.com", "endereco": "Rua A, 100"},
        {"nome": "Cliente 2", "documento": "12345678902", "telefone": "11999999992", "email": "cli2@example.com", "endereco": "Rua B, 200"},
        {"nome": "Cliente 3", "documento": "12345678903", "telefone": "11999999993", "email": "cli3@example.com", "endereco": "Rua C, 300"},
        {"nome": "Cliente 4", "documento": "12345678904", "telefone": "11999999994", "email": "cli4@example.com", "endereco": "Rua D, 400"},
        {"nome": "Cliente 5", "documento": "12345678905", "telefone": "11999999995", "email": "cli5@example.com", "endereco": "Rua E, 500"},
    ]

    for c in clientes:
        if not Cliente.query.filter_by(nome=c["nome"]).first():
            novo_cliente = Cliente(
                nome=c["nome"],
                documento=c["documento"],
                telefone=c["telefone"],
                email=c["email"],
                endereco=c["endereco"],
                ativo=True
            )
            db.session.add(novo_cliente)
        else:
            print(f"Cliente {c['nome']} já existe, pulando.")

    # --- PRODUTOS ---
    produtos = [
        {"codigo": "P0001", "nome": "Produto 1", "tipo": "tipo1", "marca": "Marca A", "unidade": UnidadeMedida.kg, "valor_unitario": 10.50, "estoque_quantidade": 100},
        {"codigo": "P0002", "nome": "Produto 2", "tipo": "tipo1", "marca": "Marca A", "unidade": UnidadeMedida.saco, "valor_unitario": 20.00, "estoque_quantidade": 50},
        {"codigo": "P0003", "nome": "Produto 3", "tipo": "tipo2", "marca": "Marca B", "unidade": UnidadeMedida.unidade, "valor_unitario": 5.00, "estoque_quantidade": 200},
        {"codigo": "P0004", "nome": "Produto 4", "tipo": "tipo2", "marca": "Marca C", "unidade": UnidadeMedida.kg, "valor_unitario": 15.00, "estoque_quantidade": 80},
        {"codigo": "P0005", "nome": "Produto 5", "tipo": "tipo3", "marca": "Marca C", "unidade": UnidadeMedida.saco, "valor_unitario": 12.00, "estoque_quantidade": 120},
        {"codigo": "P0006", "nome": "Produto 6", "tipo": "tipo3", "marca": "Marca D", "unidade": UnidadeMedida.unidade, "valor_unitario": 3.50, "estoque_quantidade": 500},
        {"codigo": "P0007", "nome": "Produto 7", "tipo": "tipo1", "marca": "Marca A", "unidade": UnidadeMedida.kg, "valor_unitario": 7.25, "estoque_quantidade": 150},
        {"codigo": "P0008", "nome": "Produto 8", "tipo": "tipo2", "marca": "Marca B", "unidade": UnidadeMedida.saco, "valor_unitario": 22.00, "estoque_quantidade": 90},
        {"codigo": "P0009", "nome": "Produto 9", "tipo": "tipo3", "marca": "Marca D", "unidade": UnidadeMedida.unidade, "valor_unitario": 9.99, "estoque_quantidade": 250},
        {"codigo": "P0010", "nome": "Produto 10", "tipo": "tipo1", "marca": "Marca A", "unidade": UnidadeMedida.kg, "valor_unitario": 11.00, "estoque_quantidade": 300},
    ]

    for p in produtos:
        if not Produto.query.filter_by(codigo=p["codigo"]).first():
            novo_produto = Produto(
                codigo=p["codigo"],
                nome=p["nome"],
                tipo=p["tipo"],
                marca=p["marca"],
                unidade=p["unidade"],
                valor_unitario=p["valor_unitario"],
                estoque_quantidade=p["estoque_quantidade"],
                ativo=True
            )
            db.session.add(novo_produto)
        else:
            print(f"Produto com código {p['codigo']} já existe, pulando.")

    # Commit das inserções
    db.session.commit()

    print("✅ Usuários, clientes e produtos cadastrados com sucesso!")
