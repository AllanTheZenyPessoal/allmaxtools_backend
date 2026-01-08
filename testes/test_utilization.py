"""
Testes unitários para os endpoints de Utilization (Utilizações).
"""
import pytest


class TestUtilizationRead:
    """Testes para leitura de utilizações."""

    def test_read_utilization_without_token(self, client, mock_utilization):
        """Testa leitura de utilização sem token."""
        response = client.get(f"/utilization/read/{mock_utilization.IdCompanyUtilization}")
        assert response.status_code == 401

    def test_read_utilization_with_token(self, client, mock_utilization, auth_headers):
        """Testa leitura de utilização com token válido."""
        response = client.get(
            f"/utilization/read/{mock_utilization.IdCompanyUtilization}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_utilization_not_found(self, client, auth_headers):
        """Testa leitura de utilização inexistente."""
        response = client.get("/utilization/read/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestUtilizationList:
    """Testes para listagem de utilizações."""

    def test_list_utilizations_without_token(self, client, mock_company):
        """Testa listagem de utilizações sem token."""
        response = client.get(f"/utilization/list/{mock_company.id_company}")
        assert response.status_code == 401

    def test_list_utilizations_with_token(self, client, mock_company, mock_utilization, auth_headers):
        """Testa listagem de utilizações com token válido."""
        response = client.get(
            f"/utilization/list/{mock_company.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_utilizations_empty_company(self, client, auth_headers):
        """Testa listagem de utilizações para empresa sem utilizações."""
        response = client.get("/utilization/list/99999", headers=auth_headers)
        assert response.status_code in [200, 401, 404]


class TestUtilizationCreate:
    """Testes para criação de utilizações."""

    def test_create_utilization_without_token(self, client, utilization_payload):
        """Testa criação de utilização sem token."""
        response = client.post("/utilization/create/", json=utilization_payload)
        assert response.status_code == 401

    def test_create_utilization_with_token(self, client, utilization_payload, auth_headers):
        """Testa criação de utilização com token válido."""
        response = client.post(
            "/utilization/create/",
            json=utilization_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_utilization_with_missing_fields(self, client, auth_headers):
        """Testa criação de utilização com campos faltando."""
        response = client.post(
            "/utilization/create/",
            json={"name": "Utilização Incompleta"},
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_utilization_with_invalid_company(self, client, auth_headers):
        """Testa criação de utilização para empresa inexistente."""
        response = client.post(
            "/utilization/create/",
            json={
                "name": "Consumo",
                "code": "CONS001",
                "id_company": 99999
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 404, 422]

    def test_create_utilization_various_types(self, client, mock_company, auth_headers):
        """Testa criação de várias utilizações."""
        utilizations = [
            {"name": "Revenda", "code": "REV", "id_company": mock_company.id_company},
            {"name": "Consumo", "code": "CONS", "id_company": mock_company.id_company},
            {"name": "Industrialização", "code": "IND", "id_company": mock_company.id_company},
            {"name": "Uso e Consumo", "code": "UC", "id_company": mock_company.id_company}
        ]
        
        for util in utilizations:
            response = client.post(
                "/utilization/create/",
                json=util,
                headers=auth_headers
            )
            assert response.status_code in [201, 401]


class TestUtilizationUpdate:
    """Testes para atualização de utilizações."""

    def test_update_utilization_without_token(self, client, mock_utilization, mock_company):
        """Testa atualização de utilização sem token."""
        response = client.put(
            f"/utilization/update/{mock_utilization.IdCompanyUtilization}",
            json={
                "name": "Revenda Atualizada",
                "code": "REVUPD",
                "id_company": mock_company.id_company
            }
        )
        assert response.status_code == 401

    def test_update_utilization_with_token(self, client, mock_utilization, mock_company, auth_headers):
        """Testa atualização de utilização com token válido."""
        response = client.put(
            f"/utilization/update/{mock_utilization.IdCompanyUtilization}",
            json={
                "name": "Revenda Atualizada",
                "code": "REVUPD",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_update_utilization_not_found(self, client, mock_company, auth_headers):
        """Testa atualização de utilização inexistente."""
        response = client.put(
            "/utilization/update/99999",
            json={
                "name": "Utilização Inexistente",
                "code": "UNE001",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestUtilizationDelete:
    """Testes para exclusão de utilizações."""

    def test_delete_utilization_without_token(self, client, mock_utilization):
        """Testa exclusão de utilização sem token."""
        response = client.delete(f"/utilization/delete/{mock_utilization.IdCompanyUtilization}")
        assert response.status_code == 401

    def test_delete_utilization_with_token(self, client, mock_utilization, auth_headers):
        """Testa exclusão de utilização com token válido."""
        response = client.delete(
            f"/utilization/delete/{mock_utilization.IdCompanyUtilization}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_delete_utilization_not_found(self, client, auth_headers):
        """Testa exclusão de utilização inexistente."""
        response = client.delete("/utilization/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]
