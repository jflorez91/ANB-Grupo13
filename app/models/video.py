from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class VideoEstado(str, Enum):
    subido = "subido"
    procesando = "procesando"
    procesado = "procesado"
    error = "error"

class VideoVisibilidad(str, Enum):
    publico = "publico"
    privado = "privado"

class VideoBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    visibilidad: VideoVisibilidad = VideoVisibilidad.publico

    @validator('titulo')
    def validate_titulo(cls, v):
        if not v or not v.strip():
            raise ValueError('El título no puede estar vacío')
        if len(v.strip()) < 3:
            raise ValueError('El título debe tener al menos 3 caracteres')
        if len(v.strip()) > 255:
            raise ValueError('El título no puede tener más de 255 caracteres')
        return v.strip()

    @validator('descripcion')
    def validate_descripcion(cls, v):
        if v and len(v) > 1000:
            raise ValueError('La descripción no puede tener más de 1000 caracteres')
        return v

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: str
    jugador_id: str
    estado: VideoEstado
    duracion_original: Optional[int] = None
    duracion_procesada: Optional[int] = None
    contador_vistas: int
    fecha_subida: datetime
    fecha_procesamiento: Optional[datetime] = None

    class Config:
        from_attributes = True

class VideoUploadResponse(BaseModel):
    video: VideoResponse
    message: str = "Video subido exitosamente. Se está procesando."