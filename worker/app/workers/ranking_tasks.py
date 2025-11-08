import logging
from celery import current_task
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.workers.ranking_tasks.update_rankings_task")
def update_rankings_task(self):
    """
    Tarea Celery para actualizar rankings - VERSIÓN WORKER INDEPENDIENTE
    """
    try:
        logger.info("📊 Ejecutando actualización de rankings desde worker...")
        
        # Importar aquí para evitar ciclos
        from app.workers.ranking_processor import RankingProcessor
        
        processor = RankingProcessor()
        result = processor.update_rankings()
        
        logger.info(f"✅ Rankings actualizados: {result}")
        return {
            "status": "success",
            "message": "Rankings actualizados exitosamente",
            "details": result,
            "task_id": self.request.id
        }
        
    except Exception as exc:
        logger.error(f"❌ Error en update_rankings_task: {str(exc)}")
        return {
            "status": "failed",
            "error": str(exc),
            "task_id": self.request.id
        }