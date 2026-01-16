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

    Args:
        app: Instância do Flask app
        file_type: Tipo de arquivo ('produtos', 'avatars', 'docs')
        subfolder: Subpasta adicional (ex: '2024/12' para organização por data)

    Returns:
        str: Caminho completo para upload
    """
    base_path = os.path.join(app.static_folder, "uploads", file_type)

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

    Args:
        photo_file: Arquivo de imagem do request.files
        app: Instância do Flask app
        produto_id: ID do produto (opcional, para nomear o arquivo)
        max_size: Tamanho máximo da imagem (largura, altura)
        quality: Qualidade da imagem (1-100)

    Returns:
        str: Caminho relativo da foto salda (a partir de static/)
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

    # Converter para webp se possível (formato mais eficiente)
    use_webp = ext in ["jpg", "jpeg", "png"] and quality > 70
    final_ext = "webp" if use_webp else ext

    if produto_id:
        filename = f"produto_{produto_id}_{name_without_ext[:20]}_{timestamp}_{unique_id}.{final_ext}"
    else:
        filename = f"{name_without_ext[:30]}_{timestamp}_{unique_id}.{final_ext}"

    # Obter caminho de upload (organizado por ano/mês)
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

        # Calcular caminho relativo
        rel_path = os.path.relpath(filepath, app.static_folder)
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
            rel_path = os.path.relpath(filepath, app.static_folder)
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
        # Converter caminho relativo para absoluto
        if photo_path.startswith("uploads/"):
            # Se já começar com uploads/, adicionar static/
            filepath = os.path.join(app.static_folder, photo_path)
        elif photo_path.startswith("/static/uploads/"):
            # Se começar com /static/uploads/, remover /static/
            filepath = os.path.join(app.static_folder, photo_path[8:])
        else:
            # Assumir que é relativo a static/
            filepath = os.path.join(app.static_folder, photo_path)

        # Verificar se o arquivo existe e deletar
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Foto deletada: {filepath}")

            # Tentar deletar pasta pai se estiver vazia
            folder = os.path.dirname(filepath)
            if os.path.exists(folder) and not os.listdir(folder):
                os.rmdir(folder)

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

    # Garantir que o caminho seja relativo a static/
    if photo_path.startswith("/"):
        # Remover barra inicial se existir
        photo_path = photo_path[1:]

    # Adicionar /static/ se necessário
    if not photo_path.startswith("static/"):
        if photo_path.startswith("uploads/"):
            photo_path = "static/" + photo_path
        else:
            photo_path = "static/uploads/produtos/" + photo_path

    # Usar url_for para gerar URL correta
    with app.app_context():
        from flask import url_for

        try:
            # Para arquivos em static/, usar url_for('static', filename=...)
            if photo_path.startswith("static/"):
                rel_path = photo_path[7:]  # Remover 'static/'
                return url_for("static", filename=rel_path, _external=False)
            else:
                return url_for("static", filename=photo_path, _external=False)
        except:
            # Fallback para construção manual
            return "/" + photo_path


def clean_temp_files(app, days_old=1):
    """Limpa arquivos temporários antigos"""
    try:
        temp_folder = os.path.join(app.static_folder, "uploads", "temp")
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
