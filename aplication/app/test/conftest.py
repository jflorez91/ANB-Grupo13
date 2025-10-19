import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Cliente de prueba simple sin base de datos"""
    with TestClient(app) as test_client:
        yield test_client