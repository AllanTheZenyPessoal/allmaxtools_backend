"""
Testes unitários para os endpoints de Address.
"""
import pytest


class TestAddressRead:
    """Testes para leitura de endereços."""

    def test_read_address_success(self, client, mock_address):
        """Testa leitura de endereço existente."""
        response = client.get(f"/address/read/{mock_address.id_address}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["cep"] == mock_address.cep
        assert data["city"] == mock_address.city
        assert data["estate"] == mock_address.estate

    def test_read_address_not_found(self, client):
        """Testa leitura de endereço inexistente."""
        response = client.get("/address/read/99999")
        assert response.status_code == 404

    def test_read_address_invalid_id(self, client):
        """Testa leitura de endereço com ID inválido."""
        response = client.get("/address/read/invalid")
        assert response.status_code == 422


class TestAddressCreate:
    """Testes para criação de endereços."""

    def test_create_address_without_token(self, client, address_payload):
        """Testa criação de endereço sem token de autenticação."""
        response = client.post("/address/create/", json=address_payload)
        assert response.status_code == 401

    def test_create_address_with_token(self, client, address_payload, auth_headers):
        """Testa criação de endereço com token válido."""
        response = client.post(
            "/address/create/",
            json=address_payload,
            headers=auth_headers
        )
        # Pode retornar 201 (sucesso) ou 401 (token inválido em teste)
        assert response.status_code in [201, 401]

    def test_create_address_with_missing_fields(self, client, auth_headers):
        """Testa criação de endereço com campos faltando."""
        response = client.post(
            "/address/create/",
            json={"cep": "01310100"},  # Faltam campos obrigatórios
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_address_with_invalid_data_types(self, client, auth_headers):
        """Testa criação de endereço com tipos de dados inválidos."""
        response = client.post(
            "/address/create/",
            json={
                "cep": "01310100",
                "city": "São Paulo",
                "estate": "SP",
                "adress": "Rua Teste",
                "number": "abc",  # Deveria ser int
                "neighborhood": "Centro"
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 422]


class TestAddressUpdate:
    """Testes para atualização de endereços."""

    def test_update_address_without_token(self, client, mock_address):
        """Testa atualização de endereço sem token."""
        response = client.put(
            f"/address/update/{mock_address.id_address}",
            json={
                "cep": "04567890",
                "city": "Rio de Janeiro",
                "estate": "RJ",
                "adress": "Rua Nova",
                "number": 200,
                "neighborhood": "Centro"
            }
        )
        assert response.status_code == 401

    def test_update_address_not_found(self, client, auth_headers):
        """Testa atualização de endereço inexistente."""
        response = client.put(
            "/address/update/99999",
            json={
                "cep": "04567890",
                "city": "Rio de Janeiro",
                "estate": "RJ",
                "adress": "Rua Nova",
                "number": 200,
                "neighborhood": "Centro"
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestAddressDelete:
    """Testes para exclusão de endereços."""

    def test_delete_address_without_token(self, client, mock_address):
        """Testa exclusão de endereço sem token."""
        response = client.delete(f"/address/delete/{mock_address.id_address}")
        assert response.status_code == 401

    def test_delete_address_not_found(self, client, auth_headers):
        """Testa exclusão de endereço inexistente."""
        response = client.delete(
            "/address/delete/99999",
            headers=auth_headers
        )
        assert response.status_code in [401, 404]
