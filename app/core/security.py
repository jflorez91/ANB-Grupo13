import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SecurityCore:
    """Lógica pura de seguridad usando bcrypt directamente"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashea la contraseña usando bcrypt directamente"""
        try:
            logger.info(f"Hasheando contraseña - Longitud: {len(password)}")
            
            # Convertir la contraseña a bytes
            password_bytes = password.encode('utf-8')
            
            # Generar salt y hash
            salt = bcrypt.gensalt(rounds=12)
            hashed_bytes = bcrypt.hashpw(password_bytes, salt)
            
            # Convertir a string para almacenar
            hashed_password = hashed_bytes.decode('utf-8')
            
            logger.info("Contraseña hasheada exitosamente")
            return hashed_password
            
        except Exception as e:
            logger.error(f"Error hasheando contraseña: {str(e)}")
            raise ValueError(f"Error procesando contraseña: {str(e)}")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica la contraseña usando bcrypt directamente"""
        try:
            # Convertir a bytes
            plain_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Verificar contraseña
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
            
        except Exception as e:
            logger.error(f"Error verificando contraseña: {str(e)}")
            return False
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> str:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            return user_id
        except JWTError:
            return None

# Instancia global
security_core = SecurityCore()