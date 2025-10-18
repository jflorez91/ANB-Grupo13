# app/workers/ranking_tasks.py
import uuid
import asyncio
from celery import current_task
from app.workers.celery_app import celery_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def update_rankings_task(self):
    """
    Tarea Celery para actualizar la tabla de rankings
    Versión que ejecuta código asíncrono
    """
    try:
        logger.info("🎯 INICIANDO TAREA DE ACTUALIZACIÓN DE RANKINGS...")
        logger.info(f"Task ID: {self.request.id}")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        
        # ✅ EJECUTAR CÓDIGO ASÍNCRONO DENTRO DE CELERY
        result = asyncio.run(_update_rankings_async())
        
        logger.info("✅ TAREA DE RANKINGS COMPLETADA EXITOSAMENTE")
        return {
            "status": "success", 
            "message": "Rankings actualizados exitosamente",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": self.request.id,
            "details": result
        }
        
    except Exception as exc:
        logger.error(f"❌ ERROR CRÍTICO EN TAREA DE RANKINGS: {str(exc)}")
        logger.exception("Detalles completos del error:")
        return {
            "status": "failed", 
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": self.request.id
        }

async def _update_rankings_async():
    """
    Función asíncrona que realiza la actualización de rankings
    """
    # Importaciones dentro de la función para evitar ciclos
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.config.settings import settings
    from app.services.ranking_service import RankingService
    
    logger.info("🔧 Configurando conexión ASÍNCRONA a base de datos...")
    
    # ✅ USAR CONEXIÓN ASÍNCRONA
    async_engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        logger.info("📊 Ejecutando servicio de rankings ASÍNCRONO...")
        ranking_service = RankingService(session)
        
        # ✅ AHORA SÍ PODEMOS USAR AWAIT
        await ranking_service.update_rankings()
    
    return {"message": "Rankings actualizados asíncronamente"}