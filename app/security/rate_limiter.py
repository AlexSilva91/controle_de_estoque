"""
Rate Limiting básico usando Redis ou memória
"""
from flask import request, jsonify, current_app
from functools import wraps
import time
import hashlib

# Cache simples em memória (substituir por Redis em produção)
_rate_limit_cache = {}

def setup_rate_limiting(app):
    """Configura rate limiting"""
    
    # Não implementa nada no momento, apenas estrutura
    # Pode ser implementado gradualmente
    pass

def rate_limit(limit=100, window=3600, key_func=None):
    """
    Decorator para rate limiting
    
    Args:
        limit: Número máximo de requisições
        window: Janela de tempo em segundos
        key_func: Função para gerar chave única
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_app.config.get('TESTING'):
                return f(*args, **kwargs)
            
            # Gera chave única para o cliente
            if key_func:
                key = key_func()
            else:
                # Usa IP + endpoint como chave padrão
                key = f"{request.remote_addr}:{request.endpoint}"
            
            current_time = time.time()
            
            # Limpa entradas antigas
            for k in list(_rate_limit_cache.keys()):
                if current_time - _rate_limit_cache[k]['timestamp'] > window:
                    _rate_limit_cache.pop(k, None)
            
            # Verifica limite
            if key in _rate_limit_cache:
                if _rate_limit_cache[key]['count'] >= limit:
                    retry_after = window - (current_time - _rate_limit_cache[key]['timestamp'])
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': int(retry_after)
                    }), 429
                _rate_limit_cache[key]['count'] += 1
            else:
                _rate_limit_cache[key] = {
                    'count': 1,
                    'timestamp': current_time
                }
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_rate_limit():
    """Rate limit específico para login"""
    def get_key():
        # Usa IP + username para prevenir brute force
        username = request.form.get('username', 'unknown')
        return hashlib.md5(
            f"{request.remote_addr}:{username}".encode()
        ).hexdigest()
    
    return rate_limit(limit=5, window=300, key_func=get_key)