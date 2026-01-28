"""
CSP UNIVERSAL - Permite TODAS as bibliotecas front-end populares
Versão: 2.0 - Resolve todos os erros reportados
"""
from flask import current_app

def setup_security_headers(app):
    """CSP que permite TUDO o que você precisa"""
    
    @app.after_request
    def add_security_headers(response):
        # Headers básicos de segurança
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
        
        # ============================================
        # CSP UNIVERSAL - PERMITE TODAS AS BIBLIOTECAS
        # ============================================
        
        # REMOVE QUALQUER CSP ANTIGO
        response.headers.pop('Content-Security-Policy', None)
        response.headers.pop('Content-Security-Policy-Report-Only', None)
        
        # LISTA COMPLETA DE TODAS AS CDNs NECESSÁRIAS
        # Baseado nos seus erros:
        all_cdns = [
            # 1. jQuery (SEU ERRO: code.jquery.com)
            'https://code.jquery.com',
            'https://ajax.googleapis.com',
            
            # 2. Bootstrap (SEU ERRO: bootstrap@5.3.0)
            'https://cdn.jsdelivr.net/npm/bootstrap@',
            'https://maxcdn.bootstrapcdn.com',
            'https://stackpath.bootstrapcdn.com',
            
            # 3. DataTables (SEU ERRO: datatables.net)
            'https://cdn.datatables.net',
            
            # 4. Select2 (SEU ERRO: select2@4.1.0)
            'https://cdn.jsdelivr.net/npm/select2@',
            
            # 5. Chart.js (SEU ERRO: chart.js)
            'https://cdn.jsdelivr.net/npm/chart.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/',
            
            # 6. Font Awesome (SEU ERRO: font-awesome)
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/',
            'https://kit.fontawesome.com',
            'https://use.fontawesome.com',
            
            # 7. Tailwind CSS (SEU ERRO: tailwindcss.com)
            'https://cdn.tailwindcss.com',
            
            # 8. Google Fonts
            'https://fonts.googleapis.com',
            'https://fonts.gstatic.com',
            
            # 9. CDNs gerais
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            'https://unpkg.com',
            
            # 10. Webfonts do Font Awesome (ERRO: webfonts)
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/',
            
            # 11. Para mapas de source (ERRO: .map files)
            'https:',
        ]
        
        # Converte lista em string
        cdn_string = ' '.join(all_cdns)
        
        # CSP COMPLETO E UNIVERSAL
        csp_directives = [
            # 1. Default
            "default-src 'self'",
            
            # 2. SCRIPT - Permite TUDO necessário
            f"script-src 'self' 'unsafe-inline' 'unsafe-eval' {cdn_string}",
            
            # 3. SCRIPT-SRC-ELEM - Para elementos <script>
            f"script-src-elem 'self' 'unsafe-inline' {cdn_string}",
            
            # 4. SCRIPT-SRC-ATTR
            f"script-src-attr 'self' 'unsafe-inline'",
            
            # 5. STYLE - Permite TUDO necessário
            f"style-src 'self' 'unsafe-inline' {cdn_string}",
            
            # 6. STYLE-SRC-ELEM - Para elementos <style> e <link rel="stylesheet">
            f"style-src-elem 'self' 'unsafe-inline' {cdn_string}",
            
            # 7. STYLE-SRC-ATTR
            f"style-src-attr 'self' 'unsafe-inline'",
            
            # 8. FONT - Permite TUDO necessário (resolve erro webfonts)
            f"font-src 'self' data: {cdn_string}",
            
            # 9. IMAGENS
            f"img-src 'self' data: blob: {cdn_string}",
            
            # 10. CONEXÕES
            f"connect-src 'self' {cdn_string}",
            
            # 11. FRAMES
            "frame-src 'self'",
            "frame-ancestors 'self'",
            
            # 12. MEDIA
            f"media-src 'self' {cdn_string}",
            
            # 13. MANIFEST
            "manifest-src 'self'",
            
            # 14. WORKER
            "worker-src 'self' blob:",
            
            # 15. OBJECT (bloqueado por segurança)
            "object-src 'none'",
            
            # 16. BASE
            "base-uri 'self'",
            
            # 17. FORM ACTION
            f"form-action 'self' {cdn_string}",
            
            # 18. REPORT - Para debug
            "report-uri /csp-violation-report-endpoint" if app.debug else "",
        ]
        
        # Remove itens vazios e junta tudo
        csp_directives = [d for d in csp_directives if d]
        csp_header = '; '.join(csp_directives)
        
        # Aplica o CSP
        response.headers['Content-Security-Policy'] = csp_header
        
        # Log para debug
        if app.debug:
            current_app.logger.info("✅ CSP Universal aplicado")
            current_app.logger.debug(f"CSP: {csp_header[:200]}...")
        
        return response
    
    return app