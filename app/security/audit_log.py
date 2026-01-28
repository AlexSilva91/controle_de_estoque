"""
Logs de auditoria de segurança
"""
import logging
from flask import request, current_app, g
import json
import time
from datetime import datetime

class SecurityLogger:
    """Logger especializado para segurança"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        
        # Configura handler de arquivo
        handler = logging.handlers.RotatingFileHandler(
            'logs/security.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type, details, user_id=None, level='INFO'):
        """
        Registra evento de segurança
        
        Args:
            event_type: Tipo do evento (login_failed, access_denied, etc.)
            details: Detalhes do evento
            user_id: ID do usuário (se disponível)
            level: Nível de log
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string,
            'endpoint': request.endpoint,
            'method': request.method,
            'details': details
        }
        
        message = json.dumps(log_entry, ensure_ascii=False)
        
        if level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)
        elif level == 'CRITICAL':
            self.logger.critical(message)
        else:
            self.logger.info(message)

def setup_audit_logging(app):
    """Configura logging de auditoria"""
    
    security_logger = SecurityLogger()
    app.security_logger = security_logger
    
    @app.before_request
    def start_audit_trail():
        g.audit_start_time = time.time()
    
    @app.after_request
    def log_access(response):
        if hasattr(g, 'audit_start_time'):
            duration = time.time() - g.audit_start_time
            
            # Log apenas para ações sensíveis
            sensitive_endpoints = ['/login', '/admin', '/api/']
            if any(request.path.startswith(ep) for ep in sensitive_endpoints):
                details = {
                    'status_code': response.status_code,
                    'duration': duration,
                    'path': request.path,
                    'method': request.method
                }
                security_logger.log_event('access', details)
        
        return response
    
    return app