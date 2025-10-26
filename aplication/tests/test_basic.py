import pytest
from fastapi import status

def test_health_check(client):
    """Test del endpoint health"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

def test_root_endpoint(client):
    """Test del endpoint raíz"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "version" in data

def test_docs_available(client):
    """Test que la documentación está disponible"""
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK

def test_redoc_available(client):
    """Test que Redoc está disponible"""
    response = client.get("/redoc")
    assert response.status_code == status.HTTP_200_OK