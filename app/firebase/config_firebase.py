import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import os
import sys
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Corrige caminho quando empacotado com PyInstaller
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

# Caminho para o arquivo de chave
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
FIREBASE_KEY_PATH = resource_path(FIREBASE_KEY_PATH)

# Inicializa o Firebase se ainda não estiver inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
    })

# Clientes prontos para uso
firestore_db = firestore.client()
firebase_auth = auth
firebase_storage = storage.bucket()

# Referências às coleções (iguais às tabelas do SQLAlchemy)
usuarios_ref = firestore_db.collection("usuarios")
produtos_ref = firestore_db.collection("produtos")
clientes_ref = firestore_db.collection("clientes")
movimentacoes_ref = firestore_db.collection("movimentacoes_estoque")
notas_fiscais_ref = firestore_db.collection("notas_fiscais")
itens_nota_ref = firestore_db.collection("nota_fiscal_itens")
financeiro_ref = firestore_db.collection("financeiro")
caixas_ref = firestore_db.collection("caixas")  
