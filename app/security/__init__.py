"""
Módulo de segurança - Integração gradual
"""
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SecurityModule:
    """Módulo principal de segurança"""
    
    def __init__(self, app=None):
        self.app = app
        self.enabled_features = set()
        
    def init_app(self, app, features=None):
        """Inicializa módulos de segurança selecionados"""
        self.app = app
        
        # Configurações padrão
        app.config.setdefault('SECURITY_ENABLED', True)
        app.config.setdefault('SECURITY_FEATURES', [
            'headers',
            'rate_limiting',
            'input_validation'
        ])
        
        if features:
            self.enabled_features = set(features)
        else:
            self.enabled_features = set(app.config.get('SECURITY_FEATURES', []))
        
        self._setup_security()
        logger.info(f"Módulo de segurança inicializado com features: {self.enabled_features}")
    
    def _setup_security(self):
        """Configura os módulos de segurança habilitados"""
        from . import headers, middleware, rate_limiter
        
        if 'headers' in self.enabled_features:
            headers.setup_security_headers(self.app)
        
        if 'middleware' in self.enabled_features:
            middleware.setup_security_middleware(self.app)
        
        if 'rate_limiting' in self.enabled_features:
            rate_limiter.setup_rate_limiting(self.app)
        
        if 'audit_log' in self.enabled_features:
            from . import audit_log
            audit_log.setup_audit_logging(self.app)

# Instância global
security = SecurityModule()