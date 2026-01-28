#!/usr/bin/env python3
"""
Testes de segurança para pytest
"""
import sys
import os

# Adiciona o diretório raiz ao PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from app import create_app
from flask import request as flask_request

@pytest.fixture
def app():
    """Cria app para testes"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    return app

@pytest.fixture
def client(app):
    """Cria cliente de teste"""
    return app.test_client()

def test_security_headers(client):
    """Testa se os headers de segurança estão configurados"""
    response = client.get('/')
    
    # Headers obrigatórios
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'
    assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    
    # CSP deve estar presente
    assert response.headers.get('Content-Security-Policy') is not None
    
    # Server header não deve expor informações
    assert 'Server' not in response.headers or 'Werkzeug' not in response.headers.get('Server', '')

def test_csp_header(client):
    """Testa Content Security Policy"""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy')
    
    assert csp is not None
    assert "'self'" in csp
    assert "default-src" in csp

def test_clickjacking_protection(client):
    """Testa proteção contra clickjacking"""
    response = client.get('/')
    frame_options = response.headers.get('X-Frame-Options')
    
    assert frame_options in ['DENY', 'SAMEORIGIN']
    
    # Testa CSP frame-ancestors também
    csp = response.headers.get('Content-Security-Policy') or ''
    assert 'frame-ancestors' in csp or 'X-Frame-Options' in response.headers

def test_security_endpoint(client):
    """Testa a rota /security-test"""
    response = client.get('/security-test')
    assert response.status_code == 200
    
    # A rota retorna JSON como string, então precisamos carregar
    try:
        data = response.get_json()
        if data is None:
            # Tenta decodificar manualmente se get_json() retornar None
            data = response.json
            if isinstance(data, str):
                import json
                data = json.loads(data)
    except:
        data = None
    
    assert data is not None, "Resposta da rota /security-test não é JSON válido"
    assert isinstance(data, dict), f"Resposta deve ser dict, mas é {type(data)}"
    
    # Verifica se tem alguma das chaves esperadas
    expected_keys = ['test', 'security_score', 'expected_headers', 'actual_headers_from_root']
    has_any_key = any(key in data for key in expected_keys)
    assert has_any_key, f"Resposta não contém nenhuma das chaves esperadas: {expected_keys}"

if __name__ == "__main__":
    # Permite executar diretamente: python test_security.py
    import sys
    sys.exit(pytest.main([__file__, '-v']))