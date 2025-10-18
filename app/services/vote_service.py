import uuid
import logging
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.schemas.video import Video
from app.schemas.voto import Voto
from app.schemas.user import User

logger = logging.getLogger(__name__)

class VoteService:
    """Servicio para gestión de votos"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def vote_for_video(self, user_id: str, video_id: str):
        """
        Registra un voto por un video
        
        Args:
            user_id: ID del usuario que vota
            video_id: ID del video a votar
            
        Raises:
            HTTPException: Si el video no existe, no es votable o ya fue votado
        """
        try:
            # 1. Verificar que el video existe y es votable
            video = await self._get_votable_video(video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video no encontrado o no disponible para votación"
                )

            # 2. Verificar que el usuario no haya votado antes por este video
            existing_vote = await self._get_existing_vote(user_id, video_id)
            if existing_vote:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya ha votado por este video"
                )

            # 3. Crear el voto
            voto = Voto(
                id=str(uuid.uuid4()),
                video_id=video_id,
                usuario_id=user_id,
                ip_address="127.0.0.1",  # En producción, obtener de request
                fecha_voto=datetime.utcnow(),
                valor=1
            )

            self.db.add(voto)
            
            # 4. Incrementar contador de vistas (opcional)
            video.contador_vistas += 1
            
            await self.db.commit()
            logger.info(f"Voto registrado: usuario {user_id} -> video {video_id}")

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error registrando voto: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )

    async def _get_votable_video(self, video_id: str):
        """Obtiene un video que cumpla con los criterios para votación"""
        result = await self.db.execute(
            select(Video).where(
                and_(
                    Video.id == video_id,
                    Video.estado == 'procesado',
                    Video.visibilidad == 'publico'
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_existing_vote(self, user_id: str, video_id: str):
        """Verifica si ya existe un voto de este usuario para este video"""
        result = await self.db.execute(
            select(Voto).where(
                and_(
                    Voto.usuario_id == user_id,
                    Voto.video_id == video_id
                )
            )
        )
        return result.scalar_one_or_none()