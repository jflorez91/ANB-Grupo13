import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.config.database import get_db
from app.api.deps import get_current_user_optional
from app.models.user import UserResponse
from app.models.video import VideoResponse
from app.services.vote_service import VoteService
from app.services.video_service import VideoService
from app.models.ranking import RankingResponse

router = APIRouter()

@router.get(
    "/videos",
    response_model=List[VideoResponse],
    summary="Listar videos para votación",
    description="Lista todos los videos públicos disponibles para votación. JWT opcional."
)
async def list_videos_for_voting(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista videos públicos disponibles para votación.
    
    Criterios:
    - Estado: 'procesado'
    - Visibilidad: 'publico'
    - Ordenados por fecha de subida (más recientes primero)
    """
    try:
        video_service = VideoService(db)
        return await video_service.get_videos_for_voting(skip, limit)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post(
    "/videos/{video_id}/vote",
    summary="Votar por un video",
    description="Emite un voto por un video público. Requiere JWT. Solo un voto por usuario por video."
)
async def vote_for_video(
    video_id: str,
    current_user: Optional[UserResponse] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Vota por un video público.
    
    Restricciones:
    - Usuario debe estar autenticado (JWT requerido)
    - Solo un voto por usuario por video
    - Video debe estar público y procesado
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
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Se requiere autenticación para votar"
            )
        
        vote_service = VoteService(db)
        await vote_service.vote_for_video(current_user.id, video_id)
        
        return {"message": "Voto registrado exitosamente."}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get(
    "/rankings",
    response_model=list[RankingResponse],  # ✅ ACTUALIZAR TIPO DE RESPUESTA
    summary="Obtener ranking de jugadores",
    description="Muestra el ranking actual de jugadores por votos acumulados. Soporta paginación y filtros por ciudad."
)
async def get_rankings(
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el ranking de jugadores ordenados por votos.
    
    Características:
    - Caching con Redis (5 minutos)
    - Paginación incluida
    - Filtro por ciudad opcional
    - Ordenamiento por votos descendente
    """
    try:
        vote_service = VoteService(db)
        rankings = await vote_service.get_rankings(
            ciudad=ciudad,
            skip=skip,
            limit=limit
        )
        
        return rankings
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )