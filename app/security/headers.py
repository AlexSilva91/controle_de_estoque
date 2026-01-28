"""
Configuração de headers de segurança HTTP
"""
from flask import after_this_request, request, current_app
import time

def setup_security_headers(app):
    """Configura headers de segurança HTTP"""
    
    @app.after_request
    def add_security_headers(response):
        # Headers básicos
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
        
        # CSP (Content Security Policy)
        if not response.headers.get('Content-Security-Policy'):
            csp_parts = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",  # Necessário para templates Flask
                "style-src 'self' 'unsafe-inline'",   # Necessário para CSS inline
                "img-src 'self' data: blob:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'self'",  # Equivalente a X-Frame-Options
                "object-src 'none'",  # Previne Flash/PDF
                "base-uri 'self'",
                "form-action 'self'",
            ]
            
            # Em produção, remova unsafe-inline se possível
            if not app.debug:
                csp_parts = [
                    "default-src 'self'",
                    "script-src 'self'",
                    "style-src 'self'",
                    "img-src 'self' data:",
                    "font-src 'self'",
                    "connect-src 'self'",
                    "frame-ancestors 'self'",
                    "object-src 'none'",
                    "base-uri 'self'",
                    "form-action 'self'",
                ]
            
            response.headers['Content-Security-Policy'] = '; '.join(csp_parts)
        
        # Remove Server header
        if 'Server' in response.headers:
            response.headers.pop('Server', None)
        
        return response
    
    return app