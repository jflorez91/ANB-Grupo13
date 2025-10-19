from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class Ranking(Base):
    __tablename__ = "Ranking"
    
    id = Column(String(36), primary_key=True, index=True)
    jugador_id = Column(String(36), ForeignKey("Jugador.id", ondelete="CASCADE"), 
                       nullable=False, index=True)
    ciudad_id = Column(String(36), ForeignKey("Ciudad.id", ondelete="CASCADE"), 
                      nullable=False, index=True)
    puntuacion_total = Column(Integer, default=0, nullable=False)
    posicion = Column(Integer, default=0, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    temporada = Column(String(10), nullable=False, comment="Ej: 2024-Q1, 2024-Q2", index=True)
    
    # Relaciones
    jugador = relationship("Jugador", back_populates="rankings")
    ciudad = relationship("Ciudad", back_populates="rankings")
    
    def __repr__(self):
        return f"<Ranking(id={self.id}, jugador_id={self.jugador_id}, posicion={self.posicion})>"
    