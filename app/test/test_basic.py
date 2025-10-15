import pytest
from fastapi import status

class TestBasicEndpoints:
    """Tests básicos que no requieren base de datos"""
    
    def test_health_check(self, client):
        """Test del endpoint health"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, client):
        """Test del endpoint raíz"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_docs_available(self, client):
        """Test que la documentación está disponible"""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    def test_redoc_available(self, client):
        """Test que Redoc está disponible"""
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK