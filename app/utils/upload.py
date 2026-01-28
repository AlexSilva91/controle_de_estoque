# app/utils/upload.py
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions):
    """Verifica se a extensão do arquivo é permitida"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_upload_path(app, file_type="produtos", subfolder=None):
    """
    Retorna o caminho completo para upload baseado no tipo de arquivo.
    AGORA USA O DIRETÓRIO FORA DA PASTA APP.

    Args:
        app: Instância do Flask app
        file_type: Tipo de arquivo ('produtos', 'avatars', 'docs')
        subfolder: Subpasta adicional (ex: '2024/12' para organização por data)

    Returns:
        str: Caminho completo para upload
    """
    # Obter o caminho base correto baseado no tipo de arquivo
    if file_type == "produtos":
        base_path = app.config.get("UPLOAD_FOLDER")
    elif file_type == "avatars":
        base_path = app.config.get("AVATAR_FOLDER")
    elif file_type == "docs":
        base_path = app.config.get("DOCS_FOLDER")
    elif file_type == "temp":
        base_path = app.config.get("TEMP_FOLDER")
    else:
        # Fallback para o diretório base de uploads
        base_path = app.config.get("UPLOAD_BASE_DIR", os.path.join(app.root_path, "uploads"))

    if subfolder:
        full_path = os.path.join(base_path, subfolder)
    else:
        # Organizar por ano/mês automaticamente
        now = datetime.now()
        year_month = now.strftime("%Y/%m")
        full_path = os.path.join(base_path, year_month)

    # Criar pasta se não existir
    os.makedirs(full_path, exist_ok=True)

    return full_path


def save_product_photo(
    photo_file, app, produto_id=None, max_size=(800, 800), quality=100
):
    """
    Salva a foto do produto e retorna o caminho relativo.
    """
    if not photo_file or photo_file.filename == "":
        return None

    # Verificar extensão
    if not allowed_file(photo_file.filename, app.config["ALLOWED_EXTENSIONS"]):
        raise ValueError(
            f'Formato de arquivo não permitido. Use: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        )

    # Gerar nome único para o arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    original_name = secure_filename(photo_file.filename)
    name_without_ext = os.path.splitext(original_name)[0]
    ext = original_name.rsplit(".", 1)[1].lower()

    # Converter para webp se possível
    use_webp = ext in ["jpg", "jpeg", "png"] and quality > 70
    final_ext = "webp" if use_webp else ext

    if produto_id:
        filename = f"produto_{produto_id}_{timestamp}_{unique_id}.{final_ext}"
    else:
        filename = f"produto_{timestamp}_{unique_id}.{final_ext}"

    # Obter caminho de upload
    upload_path = get_upload_path(app, "produtos")
    filepath = os.path.join(upload_path, filename)

    try:
        # Processar imagem
        image = Image.open(photo_file)

        # Converter para RGB se necessário
        if image.mode in ("RGBA", "P", "LA"):
            # Criar fundo branco para imagens com transparência
            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image, mask=image)
                image = background
            else:
                image = image.convert("RGB")

        # Redimensionar mantendo proporção se necessário
        if max_size:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Salvar imagem
        if use_webp:
            image.save(filepath, "WEBP", quality=quality, optimize=True)
        else:
            image.save(filepath, quality=quality, optimize=True)

        # Calcular caminho relativo (simplificado)
        upload_base = app.config.get("UPLOAD_BASE_DIR")
        if filepath.startswith(upload_base):
            rel_path = filepath[len(upload_base)+1:]  # +1 para remover a barra
        else:
            rel_path = os.path.basename(filepath)
        
        rel_path = rel_path.replace("\\", "/")  # Garantir barras normais

        logger.info(
            f"Foto salva: {rel_path} (tamanho: {os.path.getsize(filepath)} bytes)"
        )

        return rel_path

    except Exception as e:
        logger.error(f"Erro ao processar imagem {original_name}: {e}")
        # Tentar salvar o arquivo original como fallback
        try:
            photo_file.seek(0)  # Voltar ao início do arquivo
            photo_file.save(filepath)
            
            # Calcular caminho relativo
            upload_base = app.config.get("UPLOAD_BASE_DIR")
            if filepath.startswith(upload_base):
                rel_path = filepath[len(upload_base)+1:]
            else:
                rel_path = os.path.basename(filepath)
            
            rel_path = rel_path.replace("\\", "/")
            
            logger.warning(f"Imagem salva sem processamento: {rel_path}")
            return rel_path
        except Exception as save_error:
            logger.error(f"Falha ao salvar imagem original: {save_error}")
            raise


def delete_product_photo(photo_path, app):
    """Deleta a foto do produto do sistema de arquivos"""
    if not photo_path:
        return False

    try:
        # Obter o diretório base de uploads
        upload_base = app.config.get("UPLOAD_BASE_DIR")
        
        # Construir caminho completo
        if photo_path.startswith("uploads/"):
            # Se já começar com uploads/, remover o prefixo (compatibilidade)
            photo_path = photo_path[8:] if photo_path.startswith("uploads/") else photo_path
        
        filepath = os.path.join(upload_base, photo_path)

        # Verificar se o arquivo existe e deletar
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Foto deletada: {filepath}")

            # Tentar deletar pasta pai se estiver vazia
            folder = os.path.dirname(filepath)
            if os.path.exists(folder) and not os.listdir(folder):
                os.rmdir(folder)
                
                # Tentar deletar pasta avô se também estiver vazia (ano/mês)
                parent_folder = os.path.dirname(folder)
                if os.path.exists(parent_folder) and not os.listdir(parent_folder):
                    os.rmdir(parent_folder)

            return True
        else:
            logger.warning(f"Arquivo não encontrado para deleção: {filepath}")
            return False

    except Exception as e:
        logger.error(f"Erro ao deletar foto {photo_path}: {e}")
        return False


def get_product_photo_url(photo_path, app):
    """Retorna a URL completa para a foto do produto"""
    if not photo_path:
        return None

    # Se o caminho já for uma URL ou começar com http, retornar como está
    if photo_path.startswith(("http://", "https://", "//")):
        return photo_path

    # REMOVER prefixo 'uploads/' se já existir (evitar duplicação)
    if photo_path.startswith("uploads/"):
        photo_path = photo_path[8:]  # Remove 'uploads/'
    
    # Garantir que não comece com /
    if photo_path.startswith("/"):
        photo_path = photo_path[1:]

    # Usar a rota uploaded_file
    with app.app_context():
        from flask import url_for

        try:
            return url_for("uploaded_file", filename=photo_path, _external=False)
        except Exception as e:
            logger.error(f"Erro ao gerar URL para {photo_path}: {e}")
            # Fallback para URL direta
            return "/uploads/" + photo_path

def clean_temp_files(app, days_old=1):
    """Limpa arquivos temporários antigos"""
    try:
        temp_folder = app.config.get("TEMP_FOLDER")
        if not os.path.exists(temp_folder):
            return 0

        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days_old * 86400)

        for filename in os.listdir(temp_folder):
            filepath = os.path.join(temp_folder, filename)
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if file_time < cutoff_time:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Arquivo temporário deletado: {filename}")

        return deleted_count

    except Exception as e:
        logger.error(f"Erro ao limpar arquivos temporários: {e}")
        return 0


# Funções auxiliares para compatibilidade
def save_avatar(photo_file, app, user_id=None):
    """Salva foto de avatar do usuário"""
    return save_product_photo(
        photo_file, 
        app, 
        produto_id=user_id, 
        file_type="avatars", 
        max_size=(200, 200), 
        quality=80
    )


def save_document(file, app, filename_prefix=""):
    """Salva documentos diversos"""
    if not file or file.filename == "":
        return None

    # Verificar extensão
    allowed_extensions = app.config["ALLOWED_EXTENSIONS"].union(
        {"pdf", "doc", "docx", "xls", "xlsx", "txt", "xml"}
    )
    
    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError("Formato de documento não permitido")

    # Gerar nome único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    original_name = secure_filename(file.filename)
    name_without_ext = os.path.splitext(original_name)[0]
    ext = original_name.rsplit(".", 1)[1].lower()

    if filename_prefix:
        filename = f"{filename_prefix}_{name_without_ext[:20]}_{timestamp}_{unique_id}.{ext}"
    else:
        filename = f"doc_{name_without_ext[:30]}_{timestamp}_{unique_id}.{ext}"

    # Obter caminho de upload
    upload_path = get_upload_path(app, "docs")
    filepath = os.path.join(upload_path, filename)

    try:
        file.save(filepath)
        
        # Calcular caminho relativo
        upload_base = app.config.get("UPLOAD_BASE_DIR")
        rel_path = os.path.relpath(filepath, upload_base)
        rel_path = rel_path.replace("\\", "/")
        
        logger.info(f"Documento salvo: {rel_path}")
        return rel_path
        
    except Exception as e:
        logger.error(f"Erro ao salvar documento {original_name}: {e}")
        raise