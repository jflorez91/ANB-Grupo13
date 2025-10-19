from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class ProcesamientoVideo(Base):
    __tablename__ = "ProcesamientoVideo"
    
    id = Column(String(36), primary_key=True, index=True)
    video_id = Column(String(36), ForeignKey("Video.id", ondelete="CASCADE"), 
                     unique=True, nullable=False, index=True)
    tarea_id = Column(String(255), nullable=False, comment="ID de la tarea en Celery/Asynq", index=True)
    estado = Column(MySQLEnum('pendiente', 'procesando', 'completado', 'fallado', name='procesamiento_estado'), 
                   nullable=False, default='pendiente', index=True)
    intentos = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    parametros = Column(JSON, nullable=False, default=dict, comment="Parámetros de procesamiento")
    
    # Relaciones
    video = relationship("Video", back_populates="procesamiento")
    
    def __repr__(self):
        return f"<ProcesamientoVideo(id={self.id}, video_id={self.video_id}, estado={self.estado})>"