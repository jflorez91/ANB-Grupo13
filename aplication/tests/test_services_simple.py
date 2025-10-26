import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import date

from app.services.auth_service import AuthService
from app.models.user import UserCreate
from app.core.security import security_core

class TestAuthServiceSimple:
    """Tests simples del servicio de autenticación"""
    
    def test_password_hashing(self):
        """Test que el hashing de contraseñas funciona"""
        password = "TestPassword123"
        hashed = security_core.hash_password(password)
        
        # Verificar que el hash es diferente a la contraseña original
        assert hashed != password
        # Verificar que es un string
        assert isinstance(hashed, str)
        # Verificar que tiene longitud razonable
        assert len(hashed) > 20
    
    def test_password_verification(self):
        """Test que la verificación de contraseñas funciona"""
        password = "TestPassword123"
        hashed = security_core.hash_password(password)
        
        # Verificar que la contraseña correcta pasa
        assert security_core.verify_password(password, hashed) == True
        # Verificar que contraseña incorrecta falla
        assert security_core.verify_password("WrongPassword", hashed) == False

class TestSecurityCore:
    """Tests del core de seguridad"""
    
    def test_token_creation_and_verification(self):
        """Test creación y verificación de tokens JWT"""
        user_id = str(uuid.uuid4())
        
        # Crear token
        token = security_core.create_access_token({"sub": user_id})
        
        # Verificar que es un string
        assert isinstance(token, str)
        assert len(token) > 10
        
        # Verificar que se puede decodificar
        decoded_id = security_core.verify_token(token)
        assert decoded_id == user_id
    
    def test_invalid_token_returns_none(self):
        """Test que token inválido retorna None"""
        result = security_core.verify_token("invalid-token")
        assert result is None