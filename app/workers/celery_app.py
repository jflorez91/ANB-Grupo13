# app/workers/celery_app.py
from celery import Celery
from app.config.settings import settings

# Configuración de Celery con Redis como broker
celery_app = Celery(
    "anb_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.video_tasks",  # ← Asegúrate que esta ruta sea correcta
        # "app.workers.email_tasks"  # Comenta si no existe
    ]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=250,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
)

# Configuración específica para tareas de video
celery_app.conf.task_routes = {
    'app.workers.video_tasks.process_video_task': {'queue': 'video_processing'},
    'app.workers.video_tasks.cleanup_old_videos': {'queue': 'maintenance'},
}

# Importar tareas después de configurar la app
from app.workers import video_tasks