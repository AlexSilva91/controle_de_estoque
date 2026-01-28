"""
Middlewares de segurança
"""
from flask import request, abort, g, current_app
import re
import logging

logger = logging.getLogger(__name__)

def setup_security_middleware(app):
    """Configura middlewares de segurança"""
    
    @app.before_request
    def security_middleware():
        # Previne ataques comuns
        prevent_common_attacks()
        
        # Validação de conteúdo
        validate_content_type()
        
        # Sanitização básica de parâmetros
        sanitize_request_data()
    
    def prevent_common_attacks():
        """Previne ataques comuns"""
        # SQL Injection básico
        sql_keywords = [
            'union', 'select', 'insert', 'update', 'delete', 'drop',
            'truncate', 'exec', 'execute', 'script', 'javascript'
        ]
        
        for key, values in request.args.lists():
            for value in values:
                value_lower = value.lower()
                if any(keyword in value_lower for keyword in sql_keywords):
                    logger.warning(f"Possível tentativa de SQLi detectada: {key}={value}")
                    abort(400, description="Requisição inválida")
        
        # XSS básico
        xss_patterns = [
            r'<script.*?>', r'</script>', r'javascript:', 
            r'onload=', r'onerror=', r'onclick='
        ]
        
        for key, values in request.args.lists():
            for value in values:
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f"Possível tentativa de XSS detectada: {key}={value}")
                        abort(400, description="Requisição inválida")
    
    def validate_content_type():
        """Valida Content-Type para requests com corpo"""
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.content_type or ''
            
            # Verifica se é JSON esperado
            if request.is_json:
                try:
                    request.get_json()
                except Exception:
                    abort(400, description="JSON inválido")
    
    def sanitize_request_data():
        """Sanitiza dados da requisição"""
        # Remove espaços em branco excessivos
        g.clean_args = {}
        for key, values in request.args.lists():
            g.clean_args[key] = [v.strip() for v in values if v is not None]
    
    return app