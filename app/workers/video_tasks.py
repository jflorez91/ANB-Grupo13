import os
import logging
from datetime import datetime
from celery import current_task
from app.workers.celery_app import celery_app
from app.workers.video_processing import process_video_sync

# Importaciones SÍNCRONAS para base de datos
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Configuración de base de datos SÍNCRONA
sync_engine = create_engine(settings.DATABASE_URL.replace('aiomysql', 'pymysql'))
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def update_video_estado_sync(video_id: str, estado: str):
    """Actualizar estado del video - SÍNCRONO"""
    with SyncSessionLocal() as session:
        from app.schemas.video import Video
        session.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(estado=estado)
        )
        session.commit()

def update_procesamiento_estado_sync(video_id: str, estado: str, intentos: int, 
                                   fecha_inicio: datetime = None, fecha_fin: datetime = None, 
                                   error_message: str = None):
    """Actualizar estado del procesamiento - SÍNCRONO"""
    with SyncSessionLocal() as session:
        from app.schemas.procesamiento_video import ProcesamientoVideo
        update_data = {
            "estado": estado,
            "intentos": intentos
        }
        
        if fecha_inicio:
            update_data["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            update_data["fecha_fin"] = fecha_fin
        if error_message:
            update_data["error_message"] = error_message
            
        session.execute(
            update(ProcesamientoVideo)
            .where(ProcesamientoVideo.video_id == video_id)
            .values(**update_data)
        )
        session.commit()

def update_video_procesado_sync(video_id: str, archivo_procesado: str, 
                              duracion_procesada: int, resolucion_procesada: str):
    """Actualizar video procesado - SÍNCRONO"""
    with SyncSessionLocal() as session:
        from app.schemas.video import Video
        session.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(
                estado="procesado",
                archivo_procesado=archivo_procesado,
                duracion_procesada=duracion_procesada,
                resolucion_procesada=resolucion_procesada,
                fecha_procesamiento=datetime.utcnow()
            )
        )
        session.commit()

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def process_video_task(self, video_id: str):
    """
    Tarea Celery para procesar un video - VERSIÓN SÍNCRONA DEFINITIVA
    """
    try:
        logger.info(f"🎬 Iniciando procesamiento de video {video_id}")
        
        # 1. ACTUALIZAR ESTADOS A "procesando"
        update_video_estado_sync(video_id, "procesando")
        update_procesamiento_estado_sync(
            video_id, "procesando", 1, 
            fecha_inicio=datetime.utcnow()
        )
        
        # 2. PROCESAR VIDEO (SÍNCRONO)
        def progress_callback(state, meta):
            self.update_state(state=state, meta=meta)
        
        result = process_video_sync(video_id, progress_callback)
        
        # 3. VERIFICAR RESULTADO
        if result['success']:
            # ✅ ÉXITO - Actualizar como procesado
            update_video_procesado_sync(
                video_id,
                result['processed_path'],
                result['duracion_procesada'],
                result['resolucion_procesada']
            )
            update_procesamiento_estado_sync(
                video_id, "completado", 1,
                fecha_fin=datetime.utcnow()
            )
            
            logger.info(f"✅ Procesamiento completado para video {video_id}")
            return {
                'video_id': video_id,
                'status': 'completed',
                'processed_path': result['processed_path'],
                'duracion_procesada': result['duracion_procesada'],
                'message': 'Video procesado exitosamente'
            }
        else:
            # ❌ ERROR
            raise Exception(result['error'])
            
    except Exception as exc:
        logger.error(f"❌ Error procesando video {video_id}: {str(exc)}")
        
        # ACTUALIZAR ESTADO DE ERROR
        update_video_estado_sync(video_id, "error")
        update_procesamiento_estado_sync(
            video_id, "fallado", 
            self.request.retries + 1,
            fecha_fin=datetime.utcnow(),
            error_message=str(exc)
        )
        
        # Reintentar la tarea
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        else:
            logger.error(f"❌ Máximo de reintentos alcanzado para video {video_id}")
            return {
                'video_id': video_id,
                'status': 'failed',
                'error': str(exc),
                'message': 'Error procesando video después de múltiples intentos'
            }

@celery_app.task
def cleanup_old_videos():
    """Tarea de mantenimiento"""
    try:
        logger.info("Ejecutando limpieza de videos antiguos")
        return {"cleaned_files": 0, "status": "completed"}
    except Exception as e:
        logger.error(f"Error en limpieza: {str(e)}")
        return {"error": str(e), "status": "failed"}