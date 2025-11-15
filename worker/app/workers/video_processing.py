import os
import subprocess
import logging
import tempfile
from app.workers.s3_client import s3_client
from app.config.settings import settings

logger = logging.getLogger(__name__)

def process_video_s3(video_id: str):
    """Procesar video directamente desde/hacia S3"""
    try:
        logger.info(f"🎬 Procesando video S3: {video_id}")
        
        # 1. Descargar video original de S3
        s3_key_original = f"{settings.S3_UPLOAD_PREFIX}/{video_id}.mp4"
        video_content = s3_client.download_file(s3_key_original)
        
        # 2. Crear archivos temporales
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            temp_input.write(video_content)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # 3. Procesar video localmente
            result = process_video_ffmpeg(temp_input_path, temp_output_path)
            
            if result['success']:
                # 4. Leer video procesado y subir a S3
                with open(temp_output_path, "rb") as f:
                    processed_content = f.read()
                
                s3_key_processed = f"{settings.S3_PROCESSED_PREFIX}/{video_id}_final.mp4"
                processed_url = s3_client.upload_file(
                    processed_content, 
                    s3_key_processed, 
                    "video/mp4"
                )
                
                # 5. Enriquecer resultado con info S3
                result.update({
                    's3_key_processed': s3_key_processed,
                    's3_url_processed': processed_url
                })
            
            return result
            
        finally:
            # 6. Limpiar archivos temporales
            for temp_file in [temp_input_path, temp_output_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
    except Exception as e:
        logger.error(f"❌ Error procesando video S3 {video_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

def process_video_ffmpeg(input_path: str, output_path: str):
    """Procesar video con FFmpeg"""
    try:
        # Comando para recortar y procesar video
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-t', '30',              # Máximo 30 segundos
            '-s', '1280x720',        # Resolución objetivo
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-y',                    # Sobrescribir output
            output_path
        ]
        
        # Ejecutar procesamiento
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Obtener metadatos del video procesado
        duration = get_video_duration(output_path)
        
        return {
            'success': True,
            'processed_path': output_path,
            'duracion_procesada': duration,
            'resolucion_procesada': '1280x720'
        }
        
    except subprocess.CalledProcessError as e:
        return {'success': False, 'error': f"FFmpeg error: {e.stderr}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_video_duration(file_path: str):
    """Obtener duración del video procesado"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(float(result.stdout.strip()))
    except:
        return 30  # Duración por defecto