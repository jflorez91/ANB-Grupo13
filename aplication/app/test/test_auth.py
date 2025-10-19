import pytest
from fastapi import status

class TestAuthSimple:
    """Tests simples de autenticación (solo validaciones)"""
    
    def test_signup_validation(self, client):
        """Test que valida el formato del request de signup"""
        # Test con datos válidos
        response = client.post(
            "/api/auth/signup",
            json={
                "user": {
                    "email": "test@example.com",
                    "nombre": "Test",
                    "apellido": "User",
                    "password": "Password123",
                    "password_confirm": "Password123",
                    "tipo": "publico"
                }
            }
        )
        # Solo verificamos que no sea error de validación
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_signup_invalid_data(self, client):
        """Test con datos inválidos"""
        response = client.post(
            "/api/auth/signup",
            json={
                "user": {
                    "email": "invalid-email",
                    "nombre": "",
                    "apellido": "",
                    "password": "short",
                    "password_confirm": "different",
                    "tipo": "invalid"
                }
            }
        )
        # Debe fallar por validación
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_validation(self, client):
        """Test que valida el formato del request de login"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Password123"
            }
        )
        # Solo verificamos que no sea error de validación
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_invalid_email(self, client):
        """Test login con email inválido"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",
                "password": "Password123"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY