import logging
import uuid
from datetime import datetime
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.schemas.procesamiento_video import ProcesamientoVideo
from app.schemas.video import Video
from app.workers.video_processing import process_video_sync

logger = logging.getLogger(__name__)

class ProcessorService:
    def __init__(self):
        # Configurar DB connection SÍNCRONA (para workers)
        self.db_url = settings.DATABASE_URL.replace('aiomysql', 'pymysql')
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_pending_videos(self):
        """Obtener videos pendientes de procesamiento"""
        with self.SessionLocal() as session:
            result = session.execute(
                select(ProcesamientoVideo)
                .where(
                    ProcesamientoVideo.estado == 'pendiente',
                    ProcesamientoVideo.tarea_id.is_(None)
                )
                .limit(10)
            )
            return result.scalars().all()
    
    def claim_video_processing(self, procesamiento_id: str):
        """Marcar un video como siendo procesado"""
        with self.SessionLocal() as session:
            tarea_id = str(uuid.uuid4())
            session.execute(
                update(ProcesamientoVideo)
                .where(ProcesamientoVideo.id == procesamiento_id)
                .values(
                    estado='procesando',
                    tarea_id=tarea_id,
                    fecha_inicio=datetime.utcnow(),
                    intentos=ProcesamientoVideo.intentos + 1
                )
            )
            session.commit()
            return tarea_id
    
    def process_videos(self):
        """Procesar todos los videos pendientes"""
        try:
            pending_videos = self.get_pending_videos()
            
            if not pending_videos:
                logger.info("No hay videos pendientes para procesar")
                return {"processed": 0, "total_pending": 0}
            
            processed_count = 0
            for procesamiento in pending_videos:
                try:
                    # Claim el video
                    tarea_id = self.claim_video_processing(procesamiento.id)
                    logger.info(f"🎬 Procesando video {procesamiento.video_id}")
                    
                    # Procesar el video
                    result = process_video_sync(str(procesamiento.video_id))
                    
                    if result['success']:
                        self.mark_video_completed(procesamiento.video_id, result)
                        processed_count += 1
                        logger.info(f"✅ Video {procesamiento.video_id} procesado")
                    else:
                        self.mark_video_failed(procesamiento.video_id, result['error'])
                        logger.error(f"❌ Error en video {procesamiento.video_id}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando video {procesamiento.video_id}: {str(e)}")
                    self.mark_video_failed(procesamiento.video_id, str(e))
            
            return {
                "processed": processed_count, 
                "total_pending": len(pending_videos),
                "pending_remaining": len(pending_videos) - processed_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error en process_videos: {str(e)}")
            return {"error": str(e)}
    
    def mark_video_completed(self, video_id: str, result: dict):
        """Marcar video como completado"""
        with self.SessionLocal() as session:
            # Actualizar ProcesamientoVideo
            session.execute(
                update(ProcesamientoVideo)
                .where(ProcesamientoVideo.video_id == video_id)
                .values(
                    estado='completado',
                    fecha_fin=datetime.utcnow(),
                    error_message=None
                )
            )
            
            # Actualizar Video
            session.execute(
                update(Video)
                .where(Video.id == video_id)
                .values(
                    estado='procesado',
                    archivo_procesado=result['processed_path'],
                    duracion_procesada=result['duracion_procesada'],
                    resolucion_procesada=result['resolucion_procesada'],
                    fecha_procesamiento=datetime.utcnow()
                )
            )
            
            session.commit()
    
    def mark_video_failed(self, video_id: str, error_message: str):
        """Marcar video como fallado"""
        with self.SessionLocal() as session:
            session.execute(
                update(ProcesamientoVideo)
                .where(ProcesamientoVideo.video_id == video_id)
                .values(
                    estado='fallado',
                    fecha_fin=datetime.utcnow(),
                    error_message=error_message
                )
            )
            session.commit()