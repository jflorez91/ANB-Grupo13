import logging
from celery import current_task
from app.workers.celery_app import celery_app
from app.workers.processor_service import ProcessorService
from app.workers.video_processing import process_video_s3

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.workers.video_tasks.process_pending_videos_task")
def process_pending_videos_task(self):
    """
    Tarea que procesa TODOS los videos pendientes
    Se ejecuta automáticamente cada 30 segundos via Celery Beat
    """
    try:
        logger.info("🔍 Buscando videos pendientes de procesamiento...")
        
        processor = ProcessorService()
        result = processor.process_pending_videos()  # ✅ MÉTODO CORREGIDO
        
        logger.info(f"✅ Procesamiento completado. Resultado: {result}")
        return {
            "status": "success",
            "processed": result.get("processed", 0),
            "total_pending": result.get("total_pending", 0),
            "task_id": self.request.id
        }
        
    except Exception as exc:
        logger.error(f"❌ Error en process_pending_videos_task: {str(exc)}")
        return {
            "status": "failed",
            "error": str(exc),
            "task_id": self.request.id
        }

@celery_app.task(bind=True, name="app.workers.video_tasks.process_single_video_task")
def process_single_video_task(self, video_id: str):
    """
    Tarea para procesar un video específico
    Útil si quieres forzar el procesamiento de uno en particular
    """
    try:
        logger.info(f"🎬 Procesando video específico: {video_id}")
        
        processor = ProcessorService()
        
        # Buscar el procesamiento para este video
        from app.config.database import SessionLocal
        from app.schemas.procesamiento_video import ProcesamientoVideo
        
        with SessionLocal() as session:
            procesamiento = session.query(ProcesamientoVideo).filter(
                ProcesamientoVideo.video_id == video_id
            ).first()
            
            if not procesamiento:
                return {"status": "failed", "error": "Video no encontrado"}
            
            # Claim y procesar
            processor.claim_video_processing(procesamiento.id)
            result = process_video_s3(video_id)  # ✅ Procesar directamente
            
            if result['success']:
                processor.mark_video_completed(video_id, result)
                return {"status": "success", "video_id": video_id}
            else:
                processor.mark_video_failed(video_id, result['error'])
                return {"status": "failed", "error": result['error']}
                
    except Exception as exc:
        logger.error(f"❌ Error en process_single_video_task: {str(exc)}")
        return {"status": "failed", "error": str(exc)}