import pytest
from datetime import date
from pydantic import ValidationError

# Importar modelos
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import UserCreate, UserLogin
from app.models.jugador import JugadorCreate

class TestUserModels:
    """Tests de validación de modelos (sin base de datos)"""
    
    def test_valid_user_creation(self):
        """Test creación válida de usuario"""
        user = UserCreate(
            email="test@example.com",
            nombre="Juan",
            apellido="Pérez",
            password="Password123",
            password_confirm="Password123",
            tipo="publico"
        )
        assert user.email == "test@example.com"
        assert user.nombre == "Juan"
        assert user.tipo == "publico"
    
    def test_invalid_email(self):
        """Test email inválido"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                nombre="Test",
                apellido="User",
                password="Password123",
                password_confirm="Password123",
                tipo="publico"
            )
    
    def test_short_password(self):
        """Test contraseña muy corta"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                nombre="Test",
                apellido="User",
                password="short",
                password_confirm="short",
                tipo="publico"
            )
        assert "al menos 8 caracteres" in str(exc_info.value)
    
    def test_passwords_mismatch(self):
        """Test contraseñas que no coinciden"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                nombre="Test",
                apellido="User",
                password="Password123",
                password_confirm="Different123",
                tipo="publico"
            )
        assert "no coinciden" in str(exc_info.value)
    
    def test_valid_jugador_creation(self):
        """Test creación válida de jugador"""
        jugador = JugadorCreate(
            fecha_nacimiento=date(1995, 5, 15),
            ciudad_id="test-city-id",
            telefono_contacto="+573001234567",
            altura=1.85,
            peso=80.5,
            posicion="alero",
            biografia="Jugador de prueba"
        )
        assert jugador.altura == 1.85
        assert jugador.peso == 80.5
        assert jugador.posicion == "alero"

class TestUserLogin:
    """Tests del modelo de login"""
    
    def test_valid_login(self):
        """Test login válido"""
        login = UserLogin(
            email="test@example.com",
            password="ValidPassword123"
        )
        assert login.email == "test@example.com"
        assert login.password == "ValidPassword123"
    
    def test_invalid_login_email(self):
        """Test login con email inválido"""
        with pytest.raises(ValidationError):
            UserLogin(
                email="invalid-email",
                password="ValidPassword123"
            )