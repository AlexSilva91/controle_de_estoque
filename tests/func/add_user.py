from flask import Flask
from app import create_app
from app.models import db
from app.models.entities import Usuario, TipoUsuario
from passlib.context import CryptContext
from datetime import datetime

# Inicializa o app e contexto de senha
app = create_app()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dados do novo usuário
cpf = "13166456490"
senha = "842695"
nome = "Alex Alves"

with app.app_context():
    # Cria todas as tabelas do banco de dados, se ainda não existirem
    db.create_all()

    # Verifica se o usuário já existe
    usuario_existente = Usuario.query.filter_by(cpf=cpf).first()

    if usuario_existente:
        print("⚠️ Usuário já existe com esse CPF. Abortando.")
    else:
        senha_hash = pwd_context.hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            cpf=cpf,
            senha_hash=senha_hash,
            tipo=TipoUsuario.admin,
            criado_em=datetime.utcnow(),  # explicitamente define, embora tenha default
            status=True,
            sincronizado=False
        )

        db.session.add(novo_usuario)
        db.session.commit()
        print("✅ Usuário cadastrado com sucesso.")
