from sqlalchemy import Column, String, Date, DECIMAL, Text, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class Jugador(Base):
    __tablename__ = "Jugador"
    
    id = Column(String(36), primary_key=True, index=True)
    usuario_id = Column(String(36), ForeignKey("Usuario.id", ondelete="CASCADE"), 
                       unique=True, nullable=False, index=True)
    ciudad_id = Column(String(36), ForeignKey("Ciudad.id", ondelete="RESTRICT"), 
                      nullable=False, index=True)
    fecha_nacimiento = Column(Date, nullable=False)
    telefono_contacto = Column(String(20), nullable=True)
    altura = Column(DECIMAL(4, 2), nullable=True, comment="Altura en metros")
    peso = Column(DECIMAL(5, 2), nullable=True, comment="Peso en kilogramos")
    posicion = Column(MySQLEnum('base', 'escolta', 'alero', 'ala-pivot', 'pivot', name='jugador_posicion'), 
                     nullable=True)
    biografia = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    usuario = relationship("User", back_populates="jugador")
    ciudad = relationship("Ciudad", back_populates="jugadores")
    videos = relationship("Video", back_populates="jugador", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="jugador", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Jugador(id={self.id}, usuario_id={self.usuario_id}, ciudad={self.ciudad.nombre if self.ciudad else 'N/A'})>"