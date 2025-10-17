import uuid
from fastapi import APIRouter, Depends, UploadFile, File, logger, status, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.database import get_db
from app.api.deps import get_current_user
from app.models.user import UserResponse
from app.models.video import VideoCreate, VideoResponse, VideoUploadResponse, VideoDetailResponse, VideoDeleteResponse
from app.services.video_service import VideoService

router = APIRouter()

@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir video",
    description="Permite a un jugador subir un video de habilidades. Inicia procesamiento asíncrono."
)
async def upload_video(
    titulo: str = Form(..., description="Título del video"),
    file: UploadFile = File(..., description="Archivo de video MP4 (máx 100MB)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sube un video de habilidades para un jugador.

    Requiere autenticación JWT y que el usuario sea un jugador.

    Procesamiento:
    - Recorte a 30 segundos máximo
    - Ajuste de resolución a 1280x720
    - Inclusión de logo ANB
    - Procesamiento asíncrono
    """
    try:
        video_data = VideoCreate(titulo=titulo)
        video_service = VideoService(db)
        return await video_service.upload_video(current_user.id, video_data, file)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get(
    "",
    response_model=List[VideoResponse],
    summary="Listar videos del usuario",
    description="Obtiene todos los videos subidos por el usuario autenticado"
)
async def list_videos(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los videos del jugador autenticado.

    Incluye información de estado de procesamiento.
    """
    try:
        video_service = VideoService(db)
        return await video_service.get_user_videos(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get(
    "/{video_id}",
    response_model=VideoDetailResponse,
    summary="Obtener detalle de video",
    description="Obtiene el detalle de un video específico del usuario autenticado"
)
async def get_video_detail(
    video_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el detalle de un video específico del usuario.
    
    Incluye URL para ver/descargar el video si está procesado.
    Solo permite acceso a videos propios.
    """
    try:
        # Validar formato del UUID
        try:
            uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de video inválido"
            )
            
        video_service = VideoService(db)
        result = await video_service.get_video_detail(current_user.id, video_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint get_video_detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.delete(
    "/{video_id}",
    response_model=VideoDeleteResponse,
    summary="Eliminar video",
    description="Elimina un video propio si no ha sido procesado ni publicado para votación"
)
async def delete_video(
    video_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un video del usuario autenticado.
    
    Solo permite eliminar si:
    - El video no ha sido procesado (estado: 'subido' o 'error')
    - El video no ha sido publicado para votación
    - El video pertenece al usuario
    """
    try:
        video_service = VideoService(db)
        return await video_service.delete_video(current_user.id, video_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )