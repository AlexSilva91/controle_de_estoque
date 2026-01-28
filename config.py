import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False

    # ==========================
    # CONFIGURAÇÕES DE UPLOAD (FORA DA PASTA APP)
    # ==========================
    UPLOAD_BASE_DIR = os.path.join(basedir, "uploads")
    
    # Pastas específicas
    UPLOAD_FOLDER = os.path.join(UPLOAD_BASE_DIR, "produtos")
    AVATAR_FOLDER = os.path.join(UPLOAD_BASE_DIR, "avatars")
    DOCS_FOLDER = os.path.join(UPLOAD_BASE_DIR, "docs")
    TEMP_FOLDER = os.path.join(UPLOAD_BASE_DIR, "temp")
    
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo

    UPLOAD_PATHS = {
        "produtos": UPLOAD_FOLDER,
        "avatars": AVATAR_FOLDER,
        "docs": DOCS_FOLDER,
        "temp": TEMP_FOLDER,
    }

    # --- CONFIGURAÇÕES BRASIL NFe (API FISCAL) ---
    API_FISCAL_BASE_URL = os.getenv("API_FISCAL_BASE_URL", "https://api.brasilnfe.com.br/services/fiscal")
    API_FISCAL_TOKEN = os.getenv("API_FISCAL_TOKEN")
    API_FISCAL_AMBIENTE = int(os.getenv("API_FISCAL_AMBIENTE", 2))

    # ==========================
    # CONFIGURAÇÕES DE SEGURANÇA
    # ==========================
    SECURITY_ENABLED = True
    SECURITY_FEATURES = ['headers']
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = False  # Desativado inicialmente
    RATE_LIMIT_DEFAULT = "200 per day"
    
    # Validação
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
    
    # CORS (se necessário)
    CORS_ORIGINS = []  # Lista de origens permitidas

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DEV_DATABASE_URL")
        or f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
        f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB')}"
    )
    
    API_FISCAL_AMBIENTE = 2

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Ou use seu banco de teste
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False  # Desabilita CSRF para testes
    
    # Headers mais permissivos para testes
    SECURITY_FEATURES = ['headers']

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL")
        or f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
        f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB')}"
    )
    
    API_FISCAL_AMBIENTE = int(os.getenv("API_FISCAL_AMBIENTE", 1))

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig, 
    "default": DevelopmentConfig,
}