import logging
import uuid
from datetime import datetime
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.schemas.procesamiento_video import ProcesamientoVideo
from app.schemas.video import Video
from app.workers.video_processing import process_video_s3

logger = logging.getLogger(__name__)

class ProcessorService:
    def __init__(self):
        self.db_url = settings.DATABASE_URL.replace('aiomysql', 'pymysql')
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_pending_videos(self):
        """Obtener videos pendientes de procesamiento (sin tarea_id)"""
        with self.SessionLocal() as session:
            result = session.execute(
                select(ProcesamientoVideo)
                .where(
                    ProcesamientoVideo.estado == 'pendiente',
                    ProcesamientoVideo.tarea_id.is_(None)  # ✅ Solo los no asignados
                )
                .limit(5)  # Procesar en lotes pequeños
            )
            return result.scalars().all()
    
    def claim_video_processing(self, procesamiento_id: str):
        """Marcar un video como siendo procesado (asignar tarea_id)"""
        with self.SessionLocal() as session:
            tarea_id = str(uuid.uuid4())
            session.execute(
                update(ProcesamientoVideo)
                .where(ProcesamientoVideo.id == procesamiento_id)
                .values(
                    estado='procesando',
                    tarea_id=tarea_id,  # ✅ Worker asigna su propio ID
                    fecha_inicio=datetime.utcnow(),
                    intentos=ProcesamientoVideo.intentos + 1
                )
            )
            session.commit()
            return tarea_id
    
    def process_pending_videos(self):
        """Procesar todos los videos pendientes"""
        try:
            pending_videos = self.get_pending_videos()
            
            if not pending_videos:
                logger.info("⏳ No hay videos pendientes para procesar")
                return {"processed": 0, "total_pending": 0}
            
            processed_count = 0
            for procesamiento in pending_videos:
                try:
                    # Claim el video (asignar tarea_id)
                    tarea_id = self.claim_video_processing(procesamiento.id)
                    logger.info(f"🎬 Procesando video {procesamiento.video_id} - Tarea: {tarea_id}")
                    
                    # ✅ Procesar el video CON S3
                    result = process_video_s3(str(procesamiento.video_id))
                    
                    if result['success']:
                        self.mark_video_completed(procesamiento.video_id, result)
                        processed_count += 1
                        logger.info(f"✅ Video {procesamiento.video_id} procesado exitosamente")
                    else:
                        self.mark_video_failed(procesamiento.video_id, result['error'])
                        logger.error(f"❌ Error en video {procesamiento.video_id}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando video {procesamiento.video_id}: {str(e)}")
                    self.mark_video_failed(procesamiento.video_id, str(e))
            
            return {
                "processed": processed_count, 
                "total_pending": len(pending_videos)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en process_pending_videos: {str(e)}")
            return {"error": str(e)}
    
    def mark_video_completed(self, video_id: str, result: dict):
        """Marcar video como completado en S3"""
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
            
            # Actualizar Video con URLs S3 procesadas
            session.execute(
                update(Video)
                .where(Video.id == video_id)
                .values(
                    estado='procesado',
                    archivo_procesado=result['s3_key_processed'],
                    s3_url_procesado=result['s3_url_processed'],
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