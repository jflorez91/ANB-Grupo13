from fastapi import APIRouter, Depends, Form, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.config.database import get_db
from app.api.deps import get_current_user
from app.models.user import UserResponse
from app.models.video import VideoCreate, VideoResponse, VideoUploadResponse
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
    descripcion: Optional[str] = Form(None, description="Descripción del video"),
    visibilidad: str = Form("publico", description="Visibilidad del video"),
    file: UploadFile = File(..., description="Archivo de video (máx 500MB)"),
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
    video_data = VideoCreate(
        titulo=titulo,
        descripcion=descripcion,
        visibilidad=visibilidad
    )

    video_service = VideoService(db)
    return await video_service.upload_video(current_user.id, video_data, file)

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
    video_service = VideoService(db)
    return await video_service.get_user_videos(current_user.id)