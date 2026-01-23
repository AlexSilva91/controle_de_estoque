import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False

    # Configurações para upload de fotos
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads", "produtos")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo

    # Subpastas organizadas por tipo
    UPLOAD_SUBFOLDERS = {
        "produtos": "produtos",
        "avatars": "avatars",
        "docs": "docs",
        "temp": "temp",
    }

    # --- CONFIGURAÇÕES BRASIL NFe (API FISCAL) ---
    API_FISCAL_BASE_URL = os.getenv("API_FISCAL_BASE_URL", "https://api.brasilnfe.com.br/services/fiscal")
    API_FISCAL_TOKEN = os.getenv("API_FISCAL_TOKEN")
    API_FISCAL_AMBIENTE = int(os.getenv("API_FISCAL_AMBIENTE", 2))

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DEV_DATABASE_URL")
        or f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
        f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB')}"
    )
    
    API_FISCAL_AMBIENTE = 2

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
    "default": DevelopmentConfig,
}
