import os
import uuid
from fastapi import UploadFile, HTTPException, status
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

async def save_uploaded_file(file: UploadFile, subdirectory: str = "") -> str:
    """
    Guarda un archivo subido en el sistema de archivos
    """
    try:
        # Validar tipo de archivo
        if not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser un video"
            )

        # Validar extensión
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in [f'.{ext}' for ext in settings.ALLOWED_EXTENSIONS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de video no permitido. Formatos aceptados: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Crear directorio si no existe
        upload_dir = os.path.join("/storage", "uploads", subdirectory)
        os.makedirs(upload_dir, exist_ok=True)

        # Generar nombre único para el archivo
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Guardar archivo
        with open(file_path, "wb") as buffer:
            content = await file.read()
            
            # Validar tamaño del archivo
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo es demasiado grande. Tamaño máximo: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            buffer.write(content)

        logger.info(f"Archivo guardado en: {file_path}")
        return file_path

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error guardando archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error guardando el archivo"
        )

async def validate_video_file(file: UploadFile):
    """
    Valida un archivo de video
    """
    # Validar tipo MIME
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un video"
        )

    # Validar que tenga nombre
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener un nombre"
        )