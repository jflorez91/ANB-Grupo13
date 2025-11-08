from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class Voto(Base):
    __tablename__ = "Voto"
    
    id = Column(String(36), primary_key=True, index=True)
    video_id = Column(String(36), ForeignKey("Video.id", ondelete="CASCADE"), 
                     nullable=False, index=True)
    usuario_id = Column(String(36), ForeignKey("Usuario.id", ondelete="CASCADE"), 
                       nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, comment="Soporta IPv6")
    fecha_voto = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    valor = Column(Integer, default=1, nullable=False, comment="Puede ser 1 o más si hay diferentes tipos de voto")
    
    # Relaciones
    video = relationship("Video", back_populates="votos")
    usuario = relationship("User", back_populates="votos")
    
    def __repr__(self):
        return f"<Voto(id={self.id}, video_id={self.video_id}, usuario_id={self.usuario_id})>"
    