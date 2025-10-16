import os
import subprocess
import logging
from celery import current_task
from app.workers.celery_app import celery_app
from app.config.settings import settings

logger = logging.getLogger(__name__)

def process_video_with_ffmpeg(video_id: str) -> str:
    """
    Procesa el video usando FFmpeg - Función helper normal
    """
    # En una implementación real, obtendríamos la ruta del video de la base de datos
    input_path = f"/storage/uploads/videos/originales/{video_id}.mp4"
    output_path = f"/storage/processed/videos/{video_id}_processed.mp4"
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Comando FFmpeg para procesar el video
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-t', str(settings.TARGET_DURATION),  # Recortar a 30 segundos
        '-s', settings.TARGET_RESOLUTION,     # Ajustar resolución
        '-c:v', 'libx264',                    # Codec de video
        '-c:a', 'aac',                        # Codec de audio
        '-preset', 'medium',
        '-crf', '23',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"FFmpeg procesó video {video_id} exitosamente")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error en FFmpeg: {e.stderr}")
        raise Exception(f"Error procesando video con FFmpeg: {e.stderr}")

def add_anb_logo(video_path: str) -> str:
    """
    Añade el logo ANB al video - Función helper normal
    """
    output_path = video_path.replace('_processed', '_final')
    logo_path = "/storage/assets/logo_anb.png"
    
    # Verificar si el logo existe
    if not os.path.exists(logo_path):
        logger.warning(f"Logo no encontrado en {logo_path}, saltando añadir logo")
        return video_path
    
    # Comando para añadir logo (simplificado)
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', logo_path,
        '-filter_complex', '[0:v][1:v]overlay=10:10',  # Logo en esquina superior izquierda
        '-c:a', 'copy',
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        # Eliminar archivo temporal
        if os.path.exists(video_path):
            os.remove(video_path)
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error añadiendo logo: {e.stderr}")
        return video_path  # Retornar sin logo si hay error

@celery_app.task(bind=True, max_retries=3, soft_time_limit=250)
def process_video_task(self, video_id: str):
    """
    Tarea Celery para procesar un video asíncronamente
    """
    try:
        logger.info(f"Iniciando procesamiento de video {video_id}")
        
        # Fase 1: Validación
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Validando video'}
        )
        
        # Verificar que el archivo de entrada existe
        input_path = f"/storage/uploads/videos/originales/{video_id}.mp4"
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Video original no encontrado: {input_path}")
        
        # Fase 2: Procesamiento con FFmpeg
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Procesando video'}
        )
        
        processed_path = process_video_with_ffmpeg(video_id)
        
        # Fase 3: Añadir logo
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Aplicando logo ANB'}
        )
        
        final_path = add_anb_logo(processed_path)
        
        # Fase 4: Finalización
        self.update_state(
            state='PROGRESS', 
            meta={'current': 100, 'total': 100, 'status': 'Finalizando'}
        )
        
        logger.info(f"Procesamiento completado para video {video_id}")
        return {
            'video_id': video_id,
            'status': 'completed',
            'processed_path': final_path,
            'message': 'Video procesado exitosamente'
        }
        
    except Exception as exc:
        logger.error(f"Error procesando video {video_id}: {str(exc)}")
        raise self.retry(countdown=60, exc=exc)

@celery_app.task
def cleanup_old_videos():
    """
    Tarea de mantenimiento: limpiar videos antiguos
    """
    try:
        logger.info("Ejecutando limpieza de videos antiguos")
        # Por ahora solo log, implementar lógica real después
        cleaned_count = 0
        # Aquí iría la lógica real de limpieza
        
        return {"cleaned_files": cleaned_count, "status": "completed"}
    except Exception as e:
        logger.error(f"Error en limpieza: {str(e)}")
        return {"error": str(e), "status": "failed"}