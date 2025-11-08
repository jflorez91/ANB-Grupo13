import logging
import uuid
from datetime import datetime
from sqlalchemy import create_engine, select, func, desc, delete
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.schemas.ranking import Ranking
from app.schemas.jugador import Jugador
from app.schemas.video import Video
from app.schemas.voto import Voto
from app.schemas.ciudad import Ciudad
from app.schemas.user import User

logger = logging.getLogger(__name__)

class RankingProcessor:
    def __init__(self):
        self.db_url = settings.DATABASE_URL.replace('aiomysql', 'pymysql')
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def update_rankings(self):
        """Actualizar la tabla de rankings basado en votos actuales"""
        try:
            temporada = self._get_current_season()
            logger.info(f"🔄 Actualizando rankings para temporada: {temporada}")
            
            with self.SessionLocal() as session:
                # Obtener votos agrupados por jugador
                stmt = (
                    select(
                        Jugador.id.label("jugador_id"),
                        Jugador.ciudad_id,
                        User.nombre,
                        User.apellido,
                        Ciudad.nombre.label("ciudad_nombre"),
                        func.count(Voto.id).label("puntuacion_total")
                    )
                    .select_from(Jugador)
                    .join(User, User.id == Jugador.usuario_id)
                    .join(Ciudad, Ciudad.id == Jugador.ciudad_id)
                    .join(Video, Video.jugador_id == Jugador.id)
                    .join(Voto, Voto.video_id == Video.id)
                    .where(
                        Video.estado == 'procesado'
                    )
                    .group_by(Jugador.id, Jugador.ciudad_id, User.nombre, User.apellido, Ciudad.nombre)
                    .order_by(desc("puntuacion_total"))
                )
                
                result = session.execute(stmt)
                rankings_data = result.all()
                
                logger.info(f"📊 Encontrados {len(rankings_data)} jugadores con votos")
                
                if not rankings_data:
                    logger.warning("⚠️ No se encontraron jugadores con votos para ranking")
                    return {"message": "No hay datos para generar rankings"}
                
                # Limpiar rankings existentes para esta temporada
                session.execute(
                    delete(Ranking).where(Ranking.temporada == temporada)
                )
                logger.info("🗑️ Rankings antiguos eliminados")
                
                # Insertar nuevos rankings
                rankings_insertados = 0
                for position, (jugador_id, ciudad_id, nombre, apellido, ciudad_nombre, puntuacion_total) in enumerate(rankings_data, start=1):
                    ranking = Ranking(
                        id=str(uuid.uuid4()),
                        jugador_id=jugador_id,
                        ciudad_id=ciudad_id,
                        puntuacion_total=puntuacion_total,
                        posicion=position,
                        temporada=temporada,
                        fecha_actualizacion=datetime.utcnow()
                    )
                    session.add(ranking)
                    rankings_insertados += 1
                    logger.info(f"🏅 Posición {position}: {nombre} {apellido} - {ciudad_nombre} - Votos: {puntuacion_total}")
                
                session.commit()
                logger.info(f"✅ Rankings actualizados para temporada {temporada}. {rankings_insertados} registros insertados.")
                
                return {
                    "temporada": temporada,
                    "registros_insertados": rankings_insertados,
                    "jugador_top": f"{rankings_data[0][2]} {rankings_data[0][3]}" if rankings_data else None,
                    "votos_top": rankings_data[0][5] if rankings_data else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Error actualizando rankings: {str(e)}")
            raise
    
    def _get_current_season(self):
        """Obtener la temporada actual basada en el cuarto del año"""
        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1
        return f"{year}-Q{quarter}"