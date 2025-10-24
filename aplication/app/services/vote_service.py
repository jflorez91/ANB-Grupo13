import uuid
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.config.settings import settings
from app.schemas.video import Video
from app.schemas.voto import Voto
from app.schemas.user import User
from app.schemas.jugador import Jugador
from app.schemas.ciudad import Ciudad
from app.schemas.ranking import Ranking

logger = logging.getLogger(__name__)

class VoteService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.cache_ttl = 300

    async def vote_for_video(self, user_id: str, video_id: str):
       
        try:
            #Verificar que el video existe y es votable
            video = await self._get_votable_video(video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video no encontrado o no disponible para votación"
                )

            #Verificar que el usuario no haya votado antes por este video
            existing_vote = await self._get_existing_vote(user_id, video_id)
            if existing_vote:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya ha votado por este video"
                )

            #Crear el voto
            voto = Voto(
                id=str(uuid.uuid4()),
                video_id=video_id,
                usuario_id=user_id,
                ip_address="127.0.0.1",
                fecha_voto=datetime.utcnow(),
                valor=1
            )

            self.db.add(voto)
            
            #Incrementar contador de vistas (opcional)
            video.contador_vistas += 1
            
            #Invalidar cache de rankings y programar actualización
            await self.invalidate_rankings_on_vote()
            
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

    async def get_rankings(self, ciudad: str = None, skip: int = 0, limit: int = 50):
        
        try:
            # Generar clave única para el cache basada en los parámetros
            cache_key = self._generate_cache_key(ciudad, skip, limit)
            
            # Intentar obtener del cache primero
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("Ranking obtenido desde cache")
                return cached_result
            
            # Si no está en cache, calcular desde la base de datos
            logger.info("Calculando ranking desde base de datos")
            rankings = await self._calculate_rankings(ciudad, skip, limit)
            
            # Guardar en cache
            self._set_to_cache(cache_key, rankings)
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error obteniendo rankings: {str(e)}")
            # En caso de error, intentar calcular sin cache
            return await self._calculate_rankings(ciudad, skip, limit)

    async def _calculate_rankings(self, ciudad: str = None, skip: int = 0, limit: int = 50):
      
        try:
            # Primero intentar desde la tabla Ranking
            rankings = await self._calculate_rankings_from_table(ciudad, skip, limit)
            if rankings:
                return rankings
            
            # Si la tabla Ranking está vacía, usar fallback
            logger.info("Tabla Ranking vacía, usando cálculo desde votos")
            return await self._calculate_rankings_fallback(ciudad, skip, limit)
            
        except Exception as e:
            logger.error(f"Error calculando rankings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculando el ranking"
            )

    async def _calculate_rankings_from_table(self, ciudad: str = None, skip: int = 0, limit: int = 50):
        
        try:
            # Consulta optimizada usando la tabla Ranking
            stmt = (
                select(
                    Ranking.posicion,
                    User.nombre,
                    User.apellido,
                    Ciudad.nombre.label("ciudad_nombre"),
                    Ranking.puntuacion_total.label("total_votos"),
                    Jugador.id.label("player_id")
                )
                .select_from(Ranking)
                .join(Jugador, Jugador.id == Ranking.jugador_id)
                .join(User, User.id == Jugador.usuario_id)
                .join(Ciudad, Ciudad.id == Ranking.ciudad_id)
                .where(Ranking.temporada == self._get_current_season())  # Filtro por temporada actual
                .order_by(Ranking.posicion.asc())
            )
            
            # Aplicar filtro por ciudad si se proporciona
            if ciudad:
                stmt = stmt.where(Ciudad.nombre.ilike(f"%{ciudad}%"))
            
            # Aplicar paginación
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            rankings_data = result.all()
            
            # Si no hay datos en la tabla Ranking, retornar None para usar fallback
            if not rankings_data:
                return None
            
            # Formatear respuesta
            rankings = []
            for (posicion, nombre, apellido, ciudad_nombre, total_votos, player_id) in rankings_data:
                rankings.append({
                    "position": posicion,
                    "username": f"{nombre} {apellido}",
                    "city": ciudad_nombre,
                    "votes": total_votos,
                    "player_id": player_id
                })
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error calculando rankings desde tabla Ranking: {str(e)}")
            return None

    async def _calculate_rankings_fallback(self, ciudad: str = None, skip: int = 0, limit: int = 50):
        
        try:
            stmt = (
                select(
                    Jugador.id,
                    User.nombre,
                    User.apellido,
                    Ciudad.nombre.label("ciudad_nombre"),
                    func.count(Voto.id).label("total_votos")
                )
                .select_from(Jugador)
                .join(User, User.id == Jugador.usuario_id)
                .join(Ciudad, Ciudad.id == Jugador.ciudad_id)
                .join(Video, Video.jugador_id == Jugador.id)
                .join(Voto, Voto.video_id == Video.id)
                .where(
                    Video.estado == 'procesado',
                    Video.visibilidad == 'publico'
                )
                .group_by(Jugador.id, User.nombre, User.apellido, Ciudad.nombre)
                .order_by(desc("total_votos"))
            )
            
            if ciudad:
                stmt = stmt.where(Ciudad.nombre.ilike(f"%{ciudad}%"))
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            rankings_data = result.all()
            
            rankings = []
            for position, (jugador_id, nombre, apellido, ciudad_nombre, total_votos) in enumerate(rankings_data, start=skip + 1):
                rankings.append({
                    "position": position,
                    "username": f"{nombre} {apellido}",
                    "city": ciudad_nombre,
                    "votes": total_votos,
                    "player_id": jugador_id
                })
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error en fallback de rankings: {str(e)}")
            return []

    async def _get_votable_video(self, video_id: str):
        
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
        
        result = await self.db.execute(
            select(Voto).where(
                and_(
                    Voto.usuario_id == user_id,
                    Voto.video_id == video_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def invalidate_rankings_on_vote(self):
        
        try:
            # Invalidar cache inmediatamente
            await self.invalidate_rankings_cache()           
            
        except Exception as e:
            logger.warning(f"Error programando actualización de rankings: {str(e)}")

    async def invalidate_rankings_cache(self):
        
        try:
            keys = self.redis_client.keys("rankings:*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info("✅ Cache de rankings invalidado")
        except Exception as e:
            logger.warning(f"Error invalidando cache: {str(e)}")

    def _generate_cache_key(self, ciudad: str, skip: int, limit: int) -> str:
        
        base_key = "rankings"
        if ciudad:
            base_key += f":ciudad:{ciudad.lower().replace(' ', '_')}"
        base_key += f":skip:{skip}:limit:{limit}"
        return base_key

    def _get_from_cache(self, cache_key: str):
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Error accediendo al cache: {str(e)}")
            return None

    def _set_to_cache(self, cache_key: str, data):
        
        try:
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Error guardando en cache: {str(e)}")

    def _get_current_season(self):
        
        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1
        return f"{year}-Q{quarter}"