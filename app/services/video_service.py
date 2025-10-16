import uuid
import os
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.schemas.video import Video
from app.schemas.jugador import Jugador
from app.schemas.procesamiento_video import ProcesamientoVideo
from app.models.video import VideoCreate, VideoResponse, VideoUploadResponse
from app.core.storage import validate_video_file
from app.config.settings import settings
from app.workers.video_tasks import process_video_task

logger = logging.getLogger(__name__)

class VideoService:
    """Servicio para gestión de videos"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_video(self, user_id: str, video_data: VideoCreate, file: UploadFile):
        """
        Sube y procesa un video para un jugador
        """
        try:
            logger.info(f"Iniciando upload de video para usuario: {user_id}")

            # 1. Verificar que el usuario es un jugador
            jugador = await self._get_jugador_by_usuario_id(user_id)
            if not jugador:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los jugadores pueden subir videos"
                )

            # 2. Validar archivo de video
            await validate_video_file(file)

            # ✅ 3. GENERAR VIDEO_ID PRIMERO (esto es clave)
            video_id = str(uuid.uuid4())
            logger.info(f"Video ID generado: {video_id}")
            
            # ✅ 4. Guardar archivo manualmente USANDO EL VIDEO_ID
            file_extension = os.path.splitext(file.filename)[1].lower()
            file_path = f"/storage/uploads/videos/originales/{video_id}{file_extension}"
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Guardar archivo
            with open(file_path, "wb") as buffer:
                content = await file.read()
                
                # Validar tamaño del archivo
                if len(content) > settings.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El archivo es demasiado grande. Tamaño máximo: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                
                buffer.write(content)

            logger.info(f"Archivo guardado en: {file_path}")
            
            # 5. Obtener metadatos del video
            video_metadata = await self._get_video_metadata(file_path)

            # 6. Crear registro en base de datos CON EL MISMO VIDEO_ID
            video = await self._create_video_record(
                video_id=video_id,  # ← Pasar el ID generado
                jugador_id=jugador.id,
                video_data=video_data,
                file_path=file_path,
                metadata=video_metadata,
                original_filename=file.filename
            )

            # 7. Crear registro de procesamiento
            procesamiento = await self._create_processing_record(video.id)

            # 8. INICIAR PROCESAMIENTO ASÍNCRONO CON CELERY
            task = process_video_task.delay(str(video.id))
            
            # Actualizar el registro con el ID de la tarea Celery
            procesamiento.tarea_id = task.id
            await self.db.commit()

            logger.info(f"Video {video.id} creado y tarea Celery {task.id} iniciada")

            # 9. Preparar respuesta
            video_response = VideoResponse(
                id=video.id,
                jugador_id=video.jugador_id,
                titulo=video.titulo,
                descripcion=video.descripcion,
                estado=video.estado,
                duracion_original=video.duracion_original,
                duracion_procesada=video.duracion_procesada,
                contador_vistas=video.contador_vistas,
                visibilidad=video.visibilidad,
                fecha_subida=video.fecha_subida,
                fecha_procesamiento=video.fecha_procesamiento
            )

            return VideoUploadResponse(
                video=video_response,
                message=f"Video subido exitosamente. Procesamiento iniciado (Tarea: {task.id})"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error subiendo video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )

    async def _get_jugador_by_usuario_id(self, usuario_id: str):
        """Obtiene el jugador asociado a un usuario"""
        result = await self.db.execute(
            select(Jugador).where(Jugador.usuario_id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def _get_video_metadata(self, file_path: str):
        """Obtiene metadatos del video (simplificado)"""
        return {
            "duracion": 0,  # Se obtendría del video
            "resolucion": "1920x1080",  # Se obtendría del video
            "formato": os.path.splitext(file_path)[1].lower().replace('.', '')
        }

    async def _create_video_record(self, video_id: str, jugador_id: str, video_data: VideoCreate, 
                                 file_path: str, metadata: dict, original_filename: str):
        """Crea el registro del video en la base de datos"""
        
        video = Video(
            id=video_id,  # ✅ Usar el ID que ya generamos
            jugador_id=jugador_id,
            titulo=video_data.titulo,
            descripcion=video_data.descripcion,
            archivo_original=file_path,  # ✅ Esta ruta ya contiene el video_id
            duracion_original=metadata["duracion"],
            estado="subido",
            formato_original=metadata["formato"],
            tamaño_archivo=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            resolucion_original=metadata["resolucion"],
            visibilidad=video_data.visibilidad,
            fecha_subida=datetime.utcnow(),
            contador_vistas=0
        )

        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    async def _create_processing_record(self, video_id: str):
        """Crea registro de procesamiento del video"""
        
        procesamiento = ProcesamientoVideo(
            id=str(uuid.uuid4()),
            video_id=video_id,
            tarea_id=str(uuid.uuid4()),
            estado="pendiente",
            intentos=0,
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

    async def get_user_videos(self, user_id: str):
        """Obtiene todos los videos de un usuario"""
        jugador = await self._get_jugador_by_usuario_id(user_id)
        if not jugador:
            return []

        result = await self.db.execute(
            select(Video).where(Video.jugador_id == jugador.id)
        )
        videos = result.scalars().all()
        
        return [
            VideoResponse(
                id=video.id,
                jugador_id=video.jugador_id,
                titulo=video.titulo,
                descripcion=video.descripcion,
                estado=video.estado,
                duracion_original=video.duracion_original,
                duracion_procesada=video.duracion_procesada,
                contador_vistas=video.contador_vistas,
                visibilidad=video.visibilidad,
                fecha_subida=video.fecha_subida,
                fecha_procesamiento=video.fecha_procesamiento
            )
            for video in videos
        ]