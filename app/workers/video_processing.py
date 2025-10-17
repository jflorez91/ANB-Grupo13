import os
import subprocess
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

def get_video_duration(file_path: str) -> int:
    """Obtener duración del video en segundos"""
    try:
        import json
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        return int(float(metadata['format']['duration']))
    except Exception as e:
        logger.error(f"Error obteniendo duración: {e}")
        return 30

def add_logo_simple(input_path: str, output_path: str, logo_path: str) -> bool:
    """
    Añadir logo de forma SIMPLE - sin filtros complejos
    """
    try:
        # Logo estático durante todo el video
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-i', logo_path,
            '-filter_complex', 'overlay=10:10',  # Logo estático en esquina
            '-an',  # Sin audio
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("✅ Logo añadido exitosamente")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error añadiendo logo: {e.stderr}")
        return False

def process_video_sync(video_id: str, task_callback=None):
    """
    Procesar video de forma SÍNCRONA - para usar en Celery
    """
    try:
        if task_callback:
            task_callback(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Iniciando procesamiento'})
        
        logger.info(f"🎬 Iniciando procesamiento de video {video_id}")
        
        # 1. VERIFICAR ARCHIVO ORIGINAL
        input_path = f"/storage/uploads/videos/originales/{video_id}.mp4"
        if not os.path.exists(input_path):
            import glob
            pattern = f"/storage/uploads/videos/originales/{video_id}.*"
            matching_files = glob.glob(pattern)
            if not matching_files:
                raise FileNotFoundError(f"Video original no encontrado: {pattern}")
            input_path = matching_files[0]
        
        # 2. PROCESAR VIDEO - RECORTAR A 30 SEGUNDOS
        if task_callback:
            task_callback(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Recortando video'})
        
        temp_video_path = f"/storage/processed/videos/{video_id}_temp.mp4"
        os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
        
        cmd_recortar = [
            'ffmpeg',
            '-i', input_path,
            '-t', '30',              # Máximo 30 segundos
            '-s', '1280x720',        # Resolución 1280x720
            '-an',                   # Quitar audio
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-y',
            temp_video_path
        ]
        
        subprocess.run(cmd_recortar, capture_output=True, check=True)
        logger.info("✅ Video recortado y sin audio")
        
        # 3. AGREGAR LOGO NBA
        if task_callback:
            task_callback(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'Añadiendo logo NBA'})
        
        final_video_path = f"/storage/processed/videos/{video_id}_final.mp4"
        logo_path = "/storage/assets/logoANB.png"
        
        if not os.path.exists(logo_path):
            logger.warning("Logo NBA no encontrado, usando video sin logo")
            import shutil
            shutil.copy2(temp_video_path, final_video_path)
        else:
            success = add_logo_simple(temp_video_path, final_video_path, logo_path)
            if not success:
                import shutil
                shutil.copy2(temp_video_path, final_video_path)
                logger.warning("Usando video sin logo debido a error")
        
        # Limpiar archivo temporal
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        
        # 4. OBTENER METADATOS FINALES
        if task_callback:
            task_callback(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Finalizando'})
        
        duracion_procesada = get_video_duration(final_video_path)
        
        if task_callback:
            task_callback(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'Completado'})
        
        logger.info(f"✅ Procesamiento completado para video {video_id}")
        return {
            'success': True,
            'video_id': video_id,
            'processed_path': final_video_path,
            'duracion_procesada': duracion_procesada,
            'resolucion_procesada': '1280x720'
        }
        
    except Exception as exc:
        logger.error(f"❌ Error procesando video {video_id}: {str(exc)}")
        return {
            'success': False,
            'video_id': video_id,
            'error': str(exc)
        }