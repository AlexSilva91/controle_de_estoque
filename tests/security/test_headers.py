#!/usr/bin/env python3
"""
Teste rápido de headers de segurança
"""
import requests
import sys
from termcolor import colored

def test_security_headers(url):
    """Testa headers de segurança de uma URL"""
    print(f"\n🔍 Testando headers de segurança para: {url}")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        
        # Headers obrigatórios para segurança
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }
        
        # Headers recomendados
        recommended_headers = {
            'Content-Security-Policy': None,
            'Strict-Transport-Security': None,
            'Permissions-Policy': None,
        }
        
        all_headers = {**required_headers, **recommended_headers}
        
        print("\n📋 HEADERS ENCONTRADOS:")
        print("-" * 40)
        
        for header, expected_value in all_headers.items():
            actual_value = response.headers.get(header)
            
            if actual_value:
                if expected_value and actual_value == expected_value:
                    status = colored("✅ OK", "green")
                elif expected_value:
                    status = colored(f"⚠️  VALOR DIFERENTE (Esperado: {expected_value})", "yellow")
                else:
                    status = colored("✅ PRESENTE", "green")
                    
                print(f"{header}: {actual_value} {status}")
            else:
                if header in required_headers:
                    status = colored("❌ FALTANDO (OBRIGATÓRIO)", "red")
                else:
                    status = colored("⚠️  FALTANDO (RECOMENDADO)", "yellow")
                print(f"{header}: {status}")
        
        # Análise adicional
        print("\n📊 ANÁLISE ADICIONAL:")
        print("-" * 40)
        
        # Server header (deve ser omitido ou genérico)
        server_header = response.headers.get('Server')
        if server_header:
            print(f"Server: {server_header} ⚠️  (Revela tecnologia)")
        else:
            print("Server: ✅ Não exposto")
        
        # Cookies Secure/HttpOnly
        cookies = response.headers.get('Set-Cookie')
        if cookies:
            if 'Secure' in cookies and 'HttpOnly' in cookies:
                print("Cookies: ✅ Secure e HttpOnly")
            elif 'Secure' in cookies:
                print("Cookies: ⚠️  Secure mas sem HttpOnly")
            elif 'HttpOnly' in cookies:
                print("Cookies: ⚠️  HttpOnly mas sem Secure")
            else:
                print("Cookies: ❌ Sem Secure e HttpOnly")
        
        # Cabeçalhos de cache
        cache_control = response.headers.get('Cache-Control')
        if cache_control and 'no-store' in cache_control:
            print(f"Cache-Control: ✅ {cache_control}")
        else:
            print("Cache-Control: ⚠️  Configuração não ideal para dados sensíveis")
        
        print(f"\n📈 STATUS: {response.status_code}")
        print(f"⚡ TEMPO DE RESPOSTA: {response.elapsed.total_seconds():.2f}s")
        
        return response.headers
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao acessar {url}: {e}")
        return None

def detailed_csp_analysis(csp_header):
    """Faz análise detalhada do CSP"""
    print("\n🔬 ANÁLISE DETALHADA DO CSP:")
    print("-" * 40)
    
    if not csp_header:
        print("❌ CSP não configurado")
        return
    
    directives = csp_header.split(';')
    
    for directive in directives:
        directive = directive.strip()
        if not directive:
            continue
            
        if 'unsafe-inline' in directive:
            print(f"{directive} ⚠️  Permite inline scripts/styles")
        elif 'unsafe-eval' in directive:
            print(f"{directive} ❌ Permite eval() - PERIGOSO")
        elif '*' in directive:
            print(f"{directive} ❌ Permite todas as origens - PERIGOSO")
        else:
            print(f"{directive} ✅")
    
    # Verifica diretivas importantes
    required_directives = ['default-src', 'script-src', 'style-src']
    present_directives = [d.split()[0] for d in directives if d]
    
    for required in required_directives:
        if any(d.startswith(required) for d in present_directives):
            print(f"✅ {required} presente")
        else:
            print(f"❌ {required} ausente")

if __name__ == "__main__":
    # URL padrão ou da linha de comando
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "http://localhost:5000"  # Altere se necessário
    
    headers = test_security_headers(url)
    
    if headers:
        csp = headers.get('Content-Security-Policy')
        detailed_csp_analysis(csp)
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")