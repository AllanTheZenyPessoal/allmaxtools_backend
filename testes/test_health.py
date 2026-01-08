"""
Testes unitários para os endpoints de Health e Root da API.
"""
import pytest


class TestRootEndpoint:
    """Testes para o endpoint raiz (/)."""

    def test_root_endpoint_returns_message(self, client):
        """Testa se o endpoint raiz retorna a mensagem esperada."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Prototype API is running!"}

    def test_root_endpoint_method_not_allowed(self, client):
        """Testa que métodos não permitidos retornam erro."""
        response = client.post("/")
        assert response.status_code == 405


class TestHealthEndpoint:
    """Testes para o endpoint de health check (/health)."""

    def test_health_check_returns_healthy(self, client):
        """Testa se o health check retorna status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestConfigEndpoint:
    """Testes para o endpoint de configuração (/config)."""

    def test_config_endpoint_returns_configuration(self, client):
        """Testa se o endpoint de config retorna as configurações."""
        response = client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "environment" in data
        assert "version" in data
        assert "auth_required" in data
        assert "cors_enabled" in data
        assert "database" in data
        assert "endpoints" in data

    def test_config_endpoint_has_correct_version(self, client):
        """Testa se a versão está correta na configuração."""
        response = client.get("/config")
        data = response.json()
        assert data["version"] == "1.0.0"

    def test_config_endpoint_has_correct_endpoints(self, client):
        """Testa se os endpoints estão corretos na configuração."""
        response = client.get("/config")
        data = response.json()
        
        endpoints = data["endpoints"]
        assert "token_generate" in endpoints
        assert "docs" in endpoints
        assert "health" in endpoints
