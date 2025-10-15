from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.config.database import Base

class Ciudad(Base):
    __tablename__ = "Ciudad"
    
    id = Column(String(36), primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    pais = Column(String(100), default="Colombia", nullable=False)
    region = Column(String(100), nullable=False, index=True)
    activa = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    jugadores = relationship("Jugador", back_populates="ciudad", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="ciudad", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ciudad(id={self.id}, nombre={self.nombre}, region={self.region})>"