from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class SesionVoto(Base):
    __tablename__ = "SesionVoto"
    
    id = Column(String(36), primary_key=True, index=True)
    usuario_id = Column(String(36), ForeignKey("Usuario.id", ondelete="CASCADE"), 
                       nullable=False, index=True)
    token_sesion = Column(String(255), unique=True, nullable=False, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_expiracion = Column(DateTime, nullable=False, index=True)
    activa = Column(Boolean, default=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, comment="Soporta IPv6")
    
    # Relaciones
    usuario = relationship("User", back_populates="sesiones_voto")
    
    def __repr__(self):
        return f"<SesionVoto(id={self.id}, usuario_id={self.usuario_id}, activa={self.activa})>"