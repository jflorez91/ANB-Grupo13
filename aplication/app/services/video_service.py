import uuid
import os
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import subprocess
import json

from app.schemas.video import Video
from app.schemas.jugador import Jugador
from app.schemas.procesamiento_video import ProcesamientoVideo
from app.models.video import VideoCreate, VideoResponse, VideoUploadResponse, VideoDetailResponse, VideoDeleteResponse
from app.core.storage import validate_video_file
from app.config.settings import settings
from app.workers.video_tasks import process_video_task

logger = logging.getLogger(__name__)

class VideoService:
    
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_video(self, user_id: str, video_data: VideoCreate, file: UploadFile):
        
        try:
            logger.info(f"Iniciando upload de video para usuario: {user_id}")
    
            #Verificar que el usuario es un jugador
            jugador = await self._get_jugador_by_usuario_id(user_id)
            if not jugador:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Se requiere autenticación"
                )
    
            #Validar tipo de archivo - SOLO MP4
            if not file.content_type == 'video/mp4':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solo se permiten archivos MP4"
                )
    
            #Validar tamaño máximo - 100MB
            MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo es demasiado grande. Tamaño máximo: 100MB"
                )
    
            #GENERAR VIDEO_ID PRIMERO
            video_id = str(uuid.uuid4())
            logger.info(f"Video ID generado: {video_id}")
            
            #Guardar archivo manualmente USANDO EL VIDEO_ID
            file_path = f"/storage/uploads/videos/originales/{video_id}.mp4"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            #Guardar archivo
            with open(file_path, "wb") as buffer:
                buffer.write(content)
    
            logger.info(f"Archivo guardado en: {file_path}")
            
            #Obtener metadatos del video (duración real)
            video_metadata = await self._get_video_metadata(file_path)
    
            #Crear registro en base de datos
            video = await self._create_video_record(
                video_id=video_id,
                jugador_id=jugador.id,
                video_data=video_data,
                file_path=file_path,
                metadata=video_metadata,
                original_filename=file.filename
            )
    
            # Crear registro de procesamiento
            procesamiento = await self._create_processing_record(video.id)
    
            #INICIAR PROCESAMIENTO ASÍNCRONO CON CELERY
            task = process_video_task.delay(str(video.id))
            
            #Actualizar el registro con el ID de la tarea Celery
            procesamiento.tarea_id = task.id
            await self.db.commit()
    
            logger.info(f"Video {video.id} creado y tarea Celery {task.id} iniciada")
    
            #Preparar respuesta según especificación
            return VideoUploadResponse(
                message="Video subido correctamente. Procesamiento en curso.",
                task_id=task.id
            )
    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error subiendo video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )
    
    async def get_video_detail(self, user_id: str, video_id: str):
        
        try:
            #Obtener el jugador del usuario
            jugador = await self._get_jugador_by_usuario_id(user_id)
            if not jugador:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Se requiere autenticación"
                )

            #Buscar el video y verificar propiedad
            result = await self.db.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()

            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video no encontrado"
                )

            #Verificar que el usuario es propietario del video
            if video.jugador_id != jugador.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para acceder a este video"
                )

            #Construir URLs para el video (si está procesado)
            url_original = f"/storage/uploads/videos/originales/{video.id}.mp4" if video.archivo_original else None
            url_procesado = f"/storage/processed/videos/{video.id}_final.mp4" if video.archivo_procesado else None

            #Determinar si se puede eliminar
            puede_eliminar = self._puede_eliminar_video(video)

            #Retornar respuesta estructurada
            return VideoDetailResponse(
                id=video.id,
                jugador_id=video.jugador_id,
                titulo=video.titulo,
                estado=video.estado,
                duracion_original=video.duracion_original,
                duracion_procesada=video.duracion_procesada,
                contador_vistas=video.contador_vistas,
                fecha_subida=video.fecha_subida,
                fecha_procesamiento=video.fecha_procesamiento,
                url_original=url_original,
                url_procesado=url_procesado,
                puede_eliminar=puede_eliminar
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo detalle del video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )
    
    
    async def delete_video(self, user_id: str, video_id: str):
        
        try:
            #Obtener el jugador del usuario
            jugador = await self._get_jugador_by_usuario_id(user_id)
            if not jugador:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Se requiere autenticación"
                )
    
            #Buscar el video
            result = await self.db.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video no encontrado"
                )
    
            #Verificar que el usuario es propietario del video
            if video.jugador_id != jugador.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para eliminar este video"
                )
    
            #Verificar si se puede eliminar
            if not self._puede_eliminar_video(video):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El video no puede ser eliminado porque no cumple las condiciones"
                )
            
            #Eliminar archivos físicos
            try:
                if video.archivo_original and os.path.exists(video.archivo_original):
                    os.remove(video.archivo_original)
                    logger.info(f"Archivo original eliminado: {video.archivo_original}")
            
                if video.archivo_procesado and os.path.exists(video.archivo_procesado):
                    os.remove(video.archivo_procesado)
                    logger.info(f"Archivo procesado eliminado: {video.archivo_procesado}")
            except Exception as file_error:
                logger.warning(f"Error eliminando archivos físicos: {file_error}")
    
            from app.schemas.procesamiento_video import ProcesamientoVideo
            result_procesamiento = await self.db.execute(
                select(ProcesamientoVideo).where(ProcesamientoVideo.video_id == video_id)
            )
            procesamiento = result_procesamiento.scalar_one_or_none()
            if procesamiento:
                await self.db.delete(procesamiento)

            # Luego eliminar el video
            await self.db.delete(video)
            await self.db.commit()
            
            logger.info(f"Video {video_id} eliminado exitosamente por usuario {user_id}")

            return VideoDeleteResponse(
                message="El video ha sido eliminado exitosamente.",
                video_id=video_id
            )
    
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error eliminando video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )
        

    async def get_user_videos(self, user_id: str):
        
        # Primero obtener el jugador
        jugador = await self._get_jugador_by_usuario_id(user_id)
        if not jugador:
            return []

        # Obtener videos del jugador
        result = await self.db.execute(
            select(Video).where(Video.jugador_id == jugador.id)
        )
        videos = result.scalars().all()
        
        return [
            VideoResponse(
                id=video.id,
                jugador_id=video.jugador_id,
                titulo=video.titulo,
                estado=video.estado,
                duracion_original=video.duracion_original,
                duracion_procesada=video.duracion_procesada,
                contador_vistas=video.contador_vistas,
                fecha_subida=video.fecha_subida,
                fecha_procesamiento=video.fecha_procesamiento
            )
            for video in videos
        ]

    async def _get_jugador_by_usuario_id(self, usuario_id: str):
        
        result = await self.db.execute(
            select(Jugador).where(Jugador.usuario_id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def _get_video_metadata(self, file_path: str):
        
        try:
            # Comando para obtener metadatos con FFprobe
            cmd = [
                'ffprobe', 
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # Obtener duración en segundos
            duration = float(metadata['format']['duration'])
            
            # Obtener resolución
            video_stream = next((stream for stream in metadata['streams'] if stream['codec_type'] == 'video'), None)
            resolution = f"{video_stream['width']}x{video_stream['height']}" if video_stream else "1920x1080"
            
            return {
                "duracion": int(duration),  # Duración en segundos
                "resolucion": resolution,
                "formato": os.path.splitext(file_path)[1].lower().replace('.', '')
            }
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener metadatos del video: {e}")
            return {
                "duracion": 0,
                "resolucion": "1920x1080",
                "formato": os.path.splitext(file_path)[1].lower().replace('.', '')
            }

    async def _create_video_record(self, video_id: str, jugador_id: str, video_data: VideoCreate, 
                                 file_path: str, metadata: dict, original_filename: str):
        
        
        video = Video(
            id=video_id,
            jugador_id=jugador_id,
            titulo=video_data.titulo,
            archivo_original=file_path,
            duracion_original=metadata["duracion"],  # Duración real en segundos
            estado="subido",
            formato_original=metadata["formato"],
            tamaño_archivo=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            resolucion_original=metadata["resolucion"],
            fecha_subida=datetime.utcnow(),
            contador_vistas=0
        )

        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    async def _create_processing_record(self, video_id: str):
                
        procesamiento = ProcesamientoVideo(
            id=str(uuid.uuid4()),
            video_id=video_id,
            tarea_id=str(uuid.uuid4()),
            estado="pendiente",
            intentos=0,
            fecha_inicio=None,
            fecha_fin=None,
            error_message=None,
            parametros={
                "duracion_maxima": settings.TARGET_DURATION,
                "resolucion_objetivo": settings.TARGET_RESOLUTION,
                "incluir_logo": True
            }
        )

        self.db.add(procesamiento)
        await self.db.commit()
        await self.db.refresh(procesamiento)
        
        return procesamiento

    def _puede_eliminar_video(self, video) -> bool:
        
        # No se puede eliminar si está siendo procesado
        if video.estado == "procesando":
            return False
        
        # No se puede eliminar si ya está procesado y es público        
        if video.estado == "procesado" and video.visibilidad == "publico":
            return False
              
        return True
    
    
    async def get_videos_for_voting(self, skip: int = 0, limit: int = 50):
        
        try:
            from sqlalchemy import select
            from app.schemas.video import Video

            result = await self.db.execute(
                select(Video)
                .where(
                    Video.estado == 'procesado',
                    Video.visibilidad == 'publico'
                )
                .order_by(Video.fecha_subida.desc())
                .offset(skip)
                .limit(limit)
            )

            videos = result.scalars().all()

            return [
                VideoResponse(
                    id=video.id,
                    jugador_id=video.jugador_id,
                    estado=video.estado,
                    duracion_original=video.duracion_original,
                    duracion_procesada=video.duracion_procesada,
                    contador_vistas=video.contador_vistas,
                    fecha_subida=video.fecha_subida,
                    fecha_procesamiento=video.fecha_procesamiento
                )
                for video in videos
            ]

        except Exception as e:
            logger.error(f"Error obteniendo videos para votación: {str(e)}")
            return []