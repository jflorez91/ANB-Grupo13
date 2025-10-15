from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str

class UserCreate(UserBase):
    password: str
    password_confirm: str
    tipo: str = "publico"
    
    @validator('nombre', 'apellido')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre y apellido no pueden estar vacíos')
        if len(v.strip()) < 2:
            raise ValueError('El nombre y apellido deben tener al menos 2 caracteres')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', v):
            raise ValueError('El nombre y apellido solo pueden contener letras y espacios')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if len(v) > 72:
            raise ValueError('La contraseña no puede tener más de 72 caracteres')
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isupper() for char in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(char.islower() for char in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        return v
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    tipo: str
    fecha_registro: datetime
    activo: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None