from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime

class JugadorBase(BaseModel):
    fecha_nacimiento: date
    ciudad_id: str
    telefono_contacto: Optional[str] = None
    altura: Optional[float] = None
    peso: Optional[float] = None
    posicion: Optional[str] = None
    biografia: Optional[str] = None
    
    @validator('fecha_nacimiento')
    def validate_birth_date(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13:
            raise ValueError('El jugador debe tener al menos 13 años')
        if age > 50:
            raise ValueError('El jugador no puede tener más de 50 años')
        return v
    
    @validator('telefono_contacto')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace(' ', '').isdigit():
            raise ValueError('El teléfono debe contener solo números y el símbolo +')
        return v
    
    @validator('altura')
    def validate_height(cls, v):
        if v is not None and (v < 1.0 or v > 2.5):
            raise ValueError('La altura debe estar entre 1.0 y 2.5 metros')
        return v
    
    @validator('peso')
    def validate_weight(cls, v):
        if v is not None and (v < 30 or v > 150):
            raise ValueError('El peso debe estar entre 30 y 150 kg')
        return v

class JugadorCreate(JugadorBase):
    pass

class JugadorResponse(JugadorBase):
    id: str
    usuario_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True