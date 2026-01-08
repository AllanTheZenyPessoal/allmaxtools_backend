"""
Testes unitários para os endpoints de Token/Autenticação.
"""
import pytest


class TestTokenGenerate:
    """Testes para o endpoint de geração de token (/token_generate/)."""

    def test_generate_token_with_valid_credentials(self, client, superadmin_user):
        """Testa geração de token com credenciais válidas."""
        response = client.post(
            "/token_generate/",
            data={
                "username": "superadmin@gmail.com",
                "password": "123123123"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_generate_token_with_invalid_email(self, client, superadmin_user):
        """Testa geração de token com email inválido."""
        response = client.post(
            "/token_generate/",
            data={
                "username": "invalid@email.com",
                "password": "123123123"
            }
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_generate_token_with_invalid_password(self, client, superadmin_user):
        """Testa geração de token com senha inválida."""
        response = client.post(
            "/token_generate/",
            data={
                "username": "superadmin@gmail.com",
                "password": "senhaerrada"
            }
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_generate_token_without_credentials(self, client):
        """Testa geração de token sem credenciais."""
        response = client.post("/token_generate/")
        assert response.status_code == 422  # Unprocessable Entity

    def test_generate_token_with_empty_credentials(self, client):
        """Testa geração de token com credenciais vazias."""
        response = client.post(
            "/token_generate/",
            data={
                "username": "",
                "password": ""
            }
        )
        assert response.status_code in [401, 422]

    def test_token_header_is_set_on_success(self, client, superadmin_user):
        """Testa se o header Authorization é definido na resposta de sucesso."""
        response = client.post(
            "/token_generate/",
            data={
                "username": "superadmin@gmail.com",
                "password": "123123123"
            }
        )
        assert response.status_code == 200
        assert "authorization" in response.headers or "Authorization" in response.headers


class TestTokenValidation:
    """Testes para validação de tokens nas requisições."""

    def test_protected_endpoint_without_token(self, client, mock_company):
        """Testa acesso a endpoint protegido sem token."""
        response = client.get(f"/company/{mock_company.id_company}")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client, mock_company):
        """Testa acesso a endpoint protegido com token inválido."""
        response = client.get(
            f"/company/{mock_company.id_company}",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
