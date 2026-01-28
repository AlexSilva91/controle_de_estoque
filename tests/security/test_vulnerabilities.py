import requests

def test_xss_protection(url):
    """Testa se o header X-XSS-Protection funciona"""
    test_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        "<img src=x onerror=alert(1)>"
    ]
    
    for payload in test_payloads:
        response = requests.get(f"{url}?q={payload}")
        xss_header = response.headers.get('X-XSS-Protection')
        
        if xss_header and '1; mode=block' in xss_header:
            print(f"✅ XSS Protection ativado para: {payload[:30]}...")
        else:
            print(f"❌ XSS Protection não funciona para: {payload[:30]}...")

def test_clickjacking(url):
    """Testa proteção contra clickjacking"""
    response = requests.get(url)
    frame_header = response.headers.get('X-Frame-Options')
    
    if frame_header in ['DENY', 'SAMEORIGIN']:
        print(f"✅ Proteção contra clickjacking: {frame_header}")
    else:
        print("❌ Vulnerável a clickjacking")
        
    # Teste prático
    html_test = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <iframe src="{url}" width="500" height="500"></iframe>
        <p>Se você vir o site acima, está vulnerável a clickjacking</p>
    </body>
    </html>
    """
    
    with open('clickjacking_test.html', 'w') as f:
        f.write(html_test)
    print("📄 Teste salvo em clickjacking_test.html")

def test_mime_sniffing(url):
    """Testa prevenção de MIME sniffing"""
    response = requests.get(url)
    mime_header = response.headers.get('X-Content-Type-Options')
    
    if mime_header == 'nosniff':
        print("✅ Proteção contra MIME sniffing ativada")
    else:
        print("❌ Vulnerável a MIME sniffing")

if __name__ == "__main__":
    URL = "http://localhost:5000"
    
    print("🧪 Testando Vulnerabilidades Comuns")
    print("=" * 50)
    
    test_xss_protection(URL)
    test_clickjacking(URL)
    test_mime_sniffing(URL)