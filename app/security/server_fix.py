"""
Solução definitiva para remover Server header do Werkzeug
Esta solução aplica monkey patch no próprio Werkzeug
"""
import werkzeug.serving
import flask

def remove_server_header_from_werkzeug():
    """
    Aplica monkey patch no Werkzeug para nunca enviar Server header
    """
    
    # ============================================
    # 1. PATCH NO WSGIRequestHandler DO WERKZEUG
    # ============================================
    class NoServerHeaderWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
        """Request Handler que NÃO envia Server header"""
        
        # Override do método que define os headers padrão
        def send_response(self, code, message=None):
            """Envia resposta sem Server header"""
            super().send_response(code, message)
            
            # Remove Server header se existir
            if 'Server' in self.headers:
                del self.headers['Server']
        
        # Override para retornar string de versão vazia
        def version_string(self):
            return ""
        
        # Override para não logar informações sensíveis
        def log_request(self, code='-', size='-'):
            if hasattr(self, 'log'):
                self.log('info', '"%s" %s %s',
                        self.requestline, str(code), str(size))
    
    # Aplica o patch
    werkzeug.serving.WSGIRequestHandler = NoServerHeaderWSGIRequestHandler
    
    # ============================================
    # 2. PATCH NA CLASSE Response DO WERKZEUG
    # ============================================
    from werkzeug.wrappers import Response
    
    original_response_init = Response.__init__
    
    def patched_response_init(self, *args, **kwargs):
        # Chama o construtor original
        original_response_init(self, *args, **kwargs)
        
        # Remove Server header imediatamente após criação
        self.headers.pop('Server', None)
        self.headers.pop('X-Powered-By', None)
    
    Response.__init__ = patched_response_init
    
    # ============================================
    # 3. PATCH NO make_response DO FLASK
    # ============================================
    original_make_response = flask.make_response
    
    def patched_make_response(*args, **kwargs):
        response = original_make_response(*args, **kwargs)
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        return response
    
    flask.make_response = patched_make_response
    
    print("✅ Monkey patch aplicado: Server header será removido")

def setup_server_header_fix(app):
    """
    Configura a aplicação para não enviar Server header
    """
    # Aplica o monkey patch
    remove_server_header_from_werkzeug()
    
    # Middleware final de garantia
    @app.after_request
    def final_header_cleanup(response):
        """Garantia final - remove qualquer header remanescente"""
        headers_to_remove = ['Server', 'X-Powered-By', 'X-Runtime']
        for header in headers_to_remove:
            response.headers.pop(header, None)
        
        # Garante headers de segurança
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        
        return response
    
    return app