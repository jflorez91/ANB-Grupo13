from celery import Celery
import os

# Configuración para worker independiente
celery_app = Celery(
    "anb_workers",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "app.workers.video_tasks",
        "app.workers.ranking_tasks"
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

# Configuración de Celery Beat para tareas programadas
celery_app.conf.beat_schedule = {
    'process-pending-videos': {
        'task': 'app.workers.video_tasks.process_pending_videos_task',
        'schedule': 30.0,  # Cada 30 segundos
        'options': {'queue': 'video_processing'}
    },
    'update-rankings-every-5-minutes': {
        'task': 'app.workers.ranking_tasks.update_rankings_task',
        'schedule': 300.0,  # Cada 5 minutos
        'options': {'queue': 'rankings'}
    },
}

# Configuración de rutas para colas
celery_app.conf.task_routes = {
    'app.workers.video_tasks.process_pending_videos_task': {'queue': 'video_processing'},
    'app.workers.video_tasks.process_single_video_task': {'queue': 'video_processing'},
    'app.workers.ranking_tasks.update_rankings_task': {'queue': 'rankings'},
}