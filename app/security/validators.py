"""
Validadores de entrada de dados
"""
import re
import mimetypes
from werkzeug.utils import secure_filename
from flask import current_app

class InputValidator:
    """Validador de entrada de dados"""
    
    @staticmethod
    def validate_email(email):
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username):
        """Valida nome de usuário"""
        if not 3 <= len(username) <= 50:
            return False
        pattern = r'^[a-zA-Z0-9._-]+$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password(password):
        """Valida força da senha"""
        if len(password) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        
        checks = {
            'maiúscula': r'[A-Z]',
            'minúscula': r'[a-z]',
            'número': r'\d',
            'especial': r'[!@#$%^&*(),.?":{}|<>]'
        }
        
        missing = []
        for check_name, pattern in checks.items():
            if not re.search(pattern, password):
                missing.append(check_name)
        
        if missing:
            return False, f"Senha deve conter: {', '.join(missing)}"
        
        return True, "Senha válida"
    
    @staticmethod
    def sanitize_input(data, max_length=1000):
        """Sanitiza entrada de dados"""
        if isinstance(data, str):
            # Remove tags HTML/XML
            cleaned = re.sub(r'<[^>]*>', '', data)
            # Limita tamanho
            cleaned = cleaned[:max_length]
            return cleaned.strip()
        elif isinstance(data, dict):
            return {k: InputValidator.sanitize_input(v, max_length) 
                   for k, v in data.items()}
        elif isinstance(data, list):
            return [InputValidator.sanitize_input(item, max_length) 
                   for item in data]
        return data

class FileValidator:
    """Validador de arquivos"""
    
    @staticmethod
    def validate_upload(file_storage, allowed_extensions=None, max_size=None):
        """
        Valida arquivo de upload
        
        Args:
            file_storage: Objeto FileStorage do Flask
            allowed_extensions: Extensões permitidas
            max_size: Tamanho máximo em bytes
        """
        if not file_storage or not file_storage.filename:
            return False, "Nenhum arquivo enviado"
        
        # Nome seguro
        filename = secure_filename(file_storage.filename)
        
        # Verifica extensão
        if '.' in filename:
            extension = filename.rsplit('.', 1)[1].lower()
            
            if allowed_extensions and extension not in allowed_extensions:
                return False, f"Extensão não permitida: .{extension}"
        
        # Verifica tamanho
        if max_size:
            file_storage.seek(0, 2)  # Vai para o final
            file_size = file_storage.tell()
            file_storage.seek(0)  # Volta para o início
            
            if file_size > max_size:
                return False, f"Arquivo muito grande: {file_size} > {max_size}"
        
        return True, filename
    
    @staticmethod
    def get_file_mime_type(file_storage):
        """Obtém MIME type do arquivo"""
        file_storage.seek(0)
        header = file_storage.read(1024)
        file_storage.seek(0)
        
        # Verifica assinatura de arquivos perigosos
        dangerous_signatures = {
            b'<?php': 'application/x-php',
            b'<script': 'text/html',
            b'MZ': 'application/x-dosexec',  # EXE
        }
        
        for signature, mime_type in dangerous_signatures.items():
            if header.startswith(signature):
                return mime_type
        
        return mimetypes.guess_type(file_storage.filename)[0]