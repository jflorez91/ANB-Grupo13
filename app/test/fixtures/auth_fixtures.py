import uuid
from datetime import date, datetime

def create_user_data():
    """Datos de prueba para usuario"""
    return {
        "email": "test@example.com",
        "nombre": "Test",
        "apellido": "User", 
        "password": "TestPassword123",
        "password_confirm": "TestPassword123",
        "tipo": "publico"
    }

def create_jugador_data():
    """Datos de prueba para jugador"""
    return {
        "fecha_nacimiento": "1995-05-15",
        "ciudad_id": str(uuid.uuid4()),
        "telefono_contacto": "+573001234567",
        "altura": 1.85,
        "peso": 80.5,
        "posicion": "alero",
        "biografia": "Jugador de prueba"
    }

def create_login_data():
    """Datos de prueba para login"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123"
    }

def create_admin_user_data():
    """Datos de prueba para usuario admin"""
    return {
        "email": "admin@example.com",
        "nombre": "Admin",
        "apellido": "User",
        "password": "AdminPassword123",
        "password_confirm": "AdminPassword123",
        "tipo": "admin"
    }

def create_invalid_user_data():
    """Datos de prueba inválidos"""
    return {
        "email": "invalid-email",
        "nombre": "",
        "apellido": "",
        "password": "short",
        "password_confirm": "different",
        "tipo": "invalid"
    }