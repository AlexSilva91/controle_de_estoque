"""
Configurações de segurança
"""
import os

class SecurityConfig:
    # Rate Limiting
    RATE_LIMIT_DEFAULT = "200 per day; 50 per hour; 10 per minute"
    RATE_LIMIT_LOGIN = "10 per hour; 3 per minute"
    RATE_LIMIT_API = "1000 per day; 100 per hour"
    
    # Headers de segurança
    CSP_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
    }
    
    # Validação
    MAX_INPUT_LENGTH = 1000
    ALLOWED_FILE_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt'},
        'spreadsheets': {'xls', 'xlsx', 'csv'},
    }
    
    # Auditoria
    AUDIT_LOG_ENABLED = True
    AUDIT_LOG_FILE = "logs/security.log"
    
    # Autenticação
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutos em segundos
    
    @staticmethod
    def get_allowed_extensions(category='images'):
        return SecurityConfig.ALLOWED_FILE_EXTENSIONS.get(category, set())