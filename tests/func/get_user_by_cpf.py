from app.database import SessionLocal
from app.services.crud import get_usuarios,  get_user_by_cpf

# Cria uma instância da sessão
db = SessionLocal()

# Executa a função
try:
    # usuarios = get_usuarios(db)
    # for usuario in usuarios:
    #     print(usuario.nome, usuario.cpf, usuario.tipo)
    print("Buscando usuário por CPF...")
    usuario = get_user_by_cpf(db, "13166456490")  # Substitua pelo CPF desejado
    if usuario:
        print(f"Usuário encontrado: {usuario.nome}, CPF: {usuario.cpf}, Tipo: {usuario.tipo}")
    else:
        print("Usuário não encontrado com o CPF fornecido.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")
# Fecha a sessão do banco de dados
finally:
    db.close()
