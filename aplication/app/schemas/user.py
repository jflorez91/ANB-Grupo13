from sqlalchemy import Column, String, DateTime, Boolean, Enum, Text
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base 

class User(Base):
    __tablename__ = "Usuario"
    
    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tipo = Column(MySQLEnum('jugador', 'publico', 'admin', name='user_tipo'), 
                 nullable=False, default='publico')
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False)
    ultimo_login = Column(DateTime, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    jugador = relationship("Jugador", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    votos = relationship("Voto", back_populates="usuario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tipo={self.tipo})>"