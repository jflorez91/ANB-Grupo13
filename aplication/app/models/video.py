from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class VideoEstado(str, Enum):
    subido = "subido"
    procesando = "procesando"
    procesado = "procesado"
    error = "error"

    
class VideoBase(BaseModel):
    titulo: str
    @validator('titulo')
    def validate_titulo(cls, v):
        if not v or not v.strip():
            raise ValueError('El título no puede estar vacío')
        if len(v.strip()) < 3:
            raise ValueError('El título debe tener al menos 3 caracteres')
        if len(v.strip()) > 255:
            raise ValueError('El título no puede tener más de 255 caracteres')
        return v.strip()

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

class VideoDetailResponse(VideoResponse):    
    url_original: Optional[str] = None
    url_procesado: Optional[str] = None
    puede_eliminar: bool

    class Config:
        from_attributes = True

class VideoUploadResponse(BaseModel):
    message: str = "Video subido correctamente. Procesamiento en curso."
    task_id: str

class VideoDeleteResponse(BaseModel):
    message: str
    video_id: str