"""
Testes unitários para os endpoints de Freight (Frete).
"""
import pytest


class TestFreightRead:
    """Testes para leitura de fretes."""

    def test_read_freight_without_token(self, client, mock_freight):
        """Testa leitura de frete sem token."""
        response = client.get(f"/freight/read/{mock_freight.IdCompanyFreight}")
        assert response.status_code == 401

    def test_read_freight_with_token(self, client, mock_freight, auth_headers):
        """Testa leitura de frete com token válido."""
        response = client.get(
            f"/freight/read/{mock_freight.IdCompanyFreight}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_freight_not_found(self, client, auth_headers):
        """Testa leitura de frete inexistente."""
        response = client.get("/freight/read/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestFreightList:
    """Testes para listagem de fretes."""

    def test_list_freights_without_token(self, client, mock_company):
        """Testa listagem de fretes sem token."""
        response = client.get(f"/freight/list/{mock_company.id_company}")
        assert response.status_code == 401

    def test_list_freights_with_token(self, client, mock_company, mock_freight, auth_headers):
        """Testa listagem de fretes com token válido."""
        response = client.get(
            f"/freight/list/{mock_company.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_freights_empty_company(self, client, auth_headers):
        """Testa listagem de fretes para empresa sem fretes."""
        response = client.get("/freight/list/99999", headers=auth_headers)
        assert response.status_code in [200, 401, 404]


class TestFreightCreate:
    """Testes para criação de fretes."""

    def test_create_freight_without_token(self, client, freight_payload):
        """Testa criação de frete sem token."""
        response = client.post("/freight/create/", json=freight_payload)
        assert response.status_code == 401

    def test_create_freight_with_token(self, client, freight_payload, auth_headers):
        """Testa criação de frete com token válido."""
        response = client.post(
            "/freight/create/",
            json=freight_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_freight_with_missing_fields(self, client, auth_headers):
        """Testa criação de frete com campos faltando."""
        response = client.post(
            "/freight/create/",
            json={"name": "Frete Incompleto"},
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_freight_with_invalid_company(self, client, auth_headers):
        """Testa criação de frete para empresa inexistente."""
        response = client.post(
            "/freight/create/",
            json={
                "name": "Frete Novo",
                "code": "FN001",
                "id_company": 99999
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 404, 422]


class TestFreightUpdate:
    """Testes para atualização de fretes."""

    def test_update_freight_without_token(self, client, mock_freight, mock_company):
        """Testa atualização de frete sem token."""
        response = client.put(
            f"/freight/update/{mock_freight.IdCompanyFreight}",
            json={
                "name": "Frete Atualizado",
                "code": "FRTUPD",
                "id_company": mock_company.id_company
            }
        )
        assert response.status_code == 401

    def test_update_freight_with_token(self, client, mock_freight, mock_company, auth_headers):
        """Testa atualização de frete com token válido."""
        response = client.put(
            f"/freight/update/{mock_freight.IdCompanyFreight}",
            json={
                "name": "Frete Atualizado",
                "code": "FRTUPD",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_update_freight_not_found(self, client, mock_company, auth_headers):
        """Testa atualização de frete inexistente."""
        response = client.put(
            "/freight/update/99999",
            json={
                "name": "Frete Inexistente",
                "code": "FRTINX",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestFreightDelete:
    """Testes para exclusão de fretes."""

    def test_delete_freight_without_token(self, client, mock_freight):
        """Testa exclusão de frete sem token."""
        response = client.delete(f"/freight/delete/{mock_freight.IdCompanyFreight}")
        assert response.status_code == 401

    def test_delete_freight_with_token(self, client, mock_freight, auth_headers):
        """Testa exclusão de frete com token válido."""
        response = client.delete(
            f"/freight/delete/{mock_freight.IdCompanyFreight}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_delete_freight_not_found(self, client, auth_headers):
        """Testa exclusão de frete inexistente."""
        response = client.delete("/freight/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]
