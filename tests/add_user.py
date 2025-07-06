from flask import Flask
from app.models import db
from app.models.entities import Usuario, TipoUsuario
from app import create_app
from passlib.context import CryptContext

app = create_app()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cpf = "13166456491"
senha = "842695"

with app.app_context():
    db.create_all()  # Garante que as tabelas existam

    usuario_existente = Usuario.query.filter_by(cpf=cpf).first()

    if usuario_existente:
        print("⚠️ Usuário já existe com esse CPF. Abortando.")
    else:
        senha_hash = pwd_context.hash(senha)
        novo_usuario = Usuario(
            nome="Alex Alves",
            cpf=cpf,
            senha_hash=senha_hash,
            tipo=TipoUsuario.operador
        )
        db.session.add(novo_usuario)
        db.session.commit()
        print("✅ Usuário cadastrado com sucesso.")
