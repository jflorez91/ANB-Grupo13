from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class Video(Base):
    __tablename__ = "Video"
    
    id = Column(String(36), primary_key=True, index=True)
    jugador_id = Column(String(36), ForeignKey("Jugador.id", ondelete="CASCADE"), 
                       nullable=False, index=True)
    titulo = Column(String(255), nullable=False, index=True)
    archivo_original = Column(String(500), nullable=False, comment="Ruta en almacenamiento")
    archivo_procesado = Column(String(500), nullable=True, comment="Ruta del video procesado")
    duracion_original = Column(Integer, nullable=False, comment="Duración en segundos")
    duracion_procesada = Column(Integer, nullable=True, comment="Duración procesada en segundos")
    estado = Column(MySQLEnum('subido', 'procesando', 'procesado', 'error', name='video_estado'), 
                   nullable=False, default='subido', index=True)
    formato_original = Column(String(10), nullable=False, comment="mp4, avi, etc.")
    tamaño_archivo = Column(BigInteger, nullable=False, comment="Tamaño en bytes")
    resolucion_original = Column(String(20), nullable=False, comment="1920x1080, 1280x720, etc.")
    resolucion_procesada = Column(String(20), nullable=True, comment="Resolución después de procesar")
    fecha_subida = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    fecha_procesamiento = Column(DateTime, nullable=True)
    contador_vistas = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    jugador = relationship("Jugador", back_populates="videos")
    procesamiento = relationship("ProcesamientoVideo", back_populates="video", 
                                uselist=False, cascade="all, delete-orphan")
    votos = relationship("Voto", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Video(id={self.id}, titulo={self.titulo}, estado={self.estado})>"