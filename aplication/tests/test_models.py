import pytest
from datetime import date
from pydantic import ValidationError

from app.models.user import UserCreate, UserLogin
from app.models.jugador import JugadorCreate
from app.models.video import VideoCreate

class TestUserModels:
    """Tests de validación de modelos"""
    
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
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                nombre="Test",
                apellido="User",
                password="short",
                password_confirm="short",
                tipo="publico"
            )

class TestJugadorModels:
    """Tests de modelos de jugador"""
    
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

class TestVideoModels:
    """Tests de modelos de video"""
    
    def test_valid_video_creation(self):
        """Test creación válida de video"""
        video = VideoCreate(titulo="Mi video de habilidades")
        assert video.titulo == "Mi video de habilidades"
    
    def test_video_title_validation(self):
        """Test validación de título de video"""
        with pytest.raises(ValidationError):
            VideoCreate(titulo="")  # Título vacío