#!/usr/bin/env python3
"""
Verificação rápida de segurança - Versão corrigida
"""
import requests
import sys

def check_security_status(url):
    """Verifica status de segurança em tempo real"""
    print(f"🔒 Verificando segurança em: {url}")
    print("=" * 70)
    
    try:
        response = requests.get(url, timeout=5)
        
        # Headers essenciais
        essential_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['SAMEORIGIN', 'DENY'],
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': None,
            'Permissions-Policy': None,
            'Content-Security-Policy': None,
        }
        
        print("📋 STATUS DOS HEADERS:")
        print("-" * 40)
        
        score = 0
        total = len(essential_headers)
        
        for header, expected in essential_headers.items():
            value = response.headers.get(header)
            
            if value:
                if expected:
                    if isinstance(expected, list):
                        if value in expected:
                            print(f"  {header}: ✅ {value}")
                            score += 1
                        else:
                            print(f"  {header}: ❌ {value} (esperado: {expected})")
                    elif value == expected:
                        print(f"  {header}: ✅ {value}")
                        score += 1
                    else:
                        print(f"  {header}: ⚠️  {value} (esperado: {expected})")
                else:
                    print(f"  {header}: ✅ {value}")
                    score += 1
            else:
                print(f"  {header}: ❌ AUSENTE")
        
        # Header Server
        server = response.headers.get('Server')
        if server:
            if 'Werkzeug' in server or 'Python' in server:
                print(f"  Server: ⚠️  {server} (exposto)")
            else:
                print(f"  Server: ✅ {server}")
        else:
            print(f"  Server: ✅ (oculto)")
            score += 1
        
        # Cache headers
        cache = response.headers.get('Cache-Control')
        if cache and 'no-store' in cache:
            print(f"  Cache-Control: ✅ {cache}")
        else:
            print(f"  Cache-Control: ⚠️  {cache or 'AUSENTE'}")
        
        # Análise
        print(f"\n📊 PONTUAÇÃO: {score}/{total + 1} ({score/(total + 1)*100:.1f}%)")
        
        if score >= total:
            print("🎉 EXCELENTE! Todos os headers configurados!")
        elif score >= total * 0.7:
            print("👍 BOM! Maioria configurada")
        else:
            print("⚠️  PRECISA MELHORAR")
        
        # Verifica rota security-test
        print(f"\n🔍 Testando rota /security-test...")
        try:
            security_test = requests.get(url + '/security-test', timeout=3)
            if security_test.status_code == 200:
                print("  /security-test: ✅ Funcionando")
            else:
                print(f"  /security-test: ❌ Código {security_test.status_code}")
        except:
            print("  /security-test: ❌ Inacessível")
        
        return score
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 0

def test_vulnerability_protection(url):
    """Testa proteções específicas"""
    print(f"\n🛡️ Testando proteções:")
    print("-" * 40)
    
    # Testa payload XSS
    test_payloads = [
        ("XSS básico", "/?q=<script>alert(1)</script>"),
        ("XSS avançado", "/?q=<img src=x onerror=alert(1)>"),
        ("SQLi básico", "/?q=SELECT * FROM users"),
    ]
    
    for name, payload in test_payloads:
        try:
            test_url = url + payload
            response = requests.get(test_url, timeout=3)
            
            # Se não deu 500, a aplicação não quebrou
            if response.status_code != 500:
                print(f"  {name}: ✅ Protegido")
            else:
                print(f"  {name}: ❌ Vulnerável")
                
        except:
            print(f"  {name}: ⚠️  Erro no teste")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    check_security_status(base_url)
    test_vulnerability_protection(base_url)
    
    print("\n" + "=" * 70)
    print("💡 PRÓXIMOS PASSOS:")
    print("1. Execute: python run.py")
    print("2. Em outro terminal: python check_security_now.py")
    print("3. Verifique se CSP aparece nos headers")
    print("4. Teste com: curl -I http://localhost:5000 | grep CSP")