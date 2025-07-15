import threading
import time
import socket
from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import db
from .routes import init_app
from app.models.entities import Usuario
from app.firebase_sync import (
    usuarios,
    produtos,
    clientes,
    caixas,
    movimentacoes,
    notas_fiscais,
    financeiro
)

def tem_conexao():
    """Testa conexão com internet tentando abrir conexão com DNS Google."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def sincronizar_tudo(db_session):
    """Sincroniza todos os dados com o Firebase."""
    print("[SYNC] Iniciando sincronização com Firebase...")
    usuarios.sincronizar_usuarios(db_session)
    produtos.sincronizar_produtos(db_session)
    clientes.sincronizar_clientes(db_session)
    caixas.sincronizar_caixas(db_session)
    movimentacoes.sincronizar_movimentacoes(db_session)
    notas_fiscais.sincronizar_notas_fiscais(db_session)
    financeiro.sincronizar_financeiro(db_session)
    print("[SYNC] Sincronização finalizada.")

def loop_sincronizacao(Session):
    """Loop infinito que tenta sincronizar a cada 60 segundos se houver internet."""
    while True:
        if tem_conexao():
            print("[SYNC] Conexão com internet detectada. Sincronizando...")
            session = Session()
            try:
                sincronizar_tudo(session)
            except Exception as e:
                import traceback
                print("[SYNC ERROR]", traceback.format_exc())
            finally:
                session.close()
        else:
            print("[SYNC INFO] Sem conexão com internet, aguardando...")
        time.sleep(60)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa banco e migrações
    db.init_app(app)
    Migrate(app, db)

    # Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Rotas
    init_app(app)

    # Inicializa sincronização em background dentro do app context
    with app.app_context():
        Session = scoped_session(sessionmaker(bind=db.engine))
        sync_thread = threading.Thread(target=loop_sincronizacao, args=(Session,), daemon=True)
        sync_thread.start()

    return app
