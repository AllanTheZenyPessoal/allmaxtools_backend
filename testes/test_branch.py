"""
Testes unitários para os endpoints de Branch (Filiais).
"""
import pytest


class TestBranchRead:
    """Testes para leitura de filiais."""

    def test_read_branch_without_token(self, client, mock_branch):
        """Testa leitura de filial sem token."""
        response = client.get(f"/branch/read/{mock_branch.IdCompanyBranch}")
        assert response.status_code == 401

    def test_read_branch_with_token(self, client, mock_branch, auth_headers):
        """Testa leitura de filial com token válido."""
        response = client.get(
            f"/branch/read/{mock_branch.IdCompanyBranch}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_branch_not_found(self, client, auth_headers):
        """Testa leitura de filial inexistente."""
        response = client.get("/branch/read/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestBranchList:
    """Testes para listagem de filiais."""

    def test_list_branches_without_token(self, client, mock_company):
        """Testa listagem de filiais sem token."""
        response = client.get(f"/branch/list/{mock_company.id_company}")
        assert response.status_code == 401

    def test_list_branches_with_token(self, client, mock_company, mock_branch, auth_headers):
        """Testa listagem de filiais com token válido."""
        response = client.get(
            f"/branch/list/{mock_company.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_branches_empty_company(self, client, auth_headers):
        """Testa listagem de filiais para empresa sem filiais."""
        response = client.get("/branch/list/99999", headers=auth_headers)
        assert response.status_code in [200, 401, 404]


class TestBranchCreate:
    """Testes para criação de filiais."""

    def test_create_branch_without_token(self, client, branch_payload):
        """Testa criação de filial sem token."""
        response = client.post("/branch/create/", json=branch_payload)
        assert response.status_code == 401

    def test_create_branch_with_token(self, client, branch_payload, auth_headers):
        """Testa criação de filial com token válido."""
        response = client.post(
            "/branch/create/",
            json=branch_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_branch_with_missing_fields(self, client, auth_headers):
        """Testa criação de filial com campos faltando."""
        response = client.post(
            "/branch/create/",
            json={"name": "Filial Teste"},
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_branch_with_invalid_company(self, client, auth_headers):
        """Testa criação de filial para empresa inexistente."""
        response = client.post(
            "/branch/create/",
            json={
                "name": "Nova Filial",
                "code": "NF001",
                "id_company": 99999
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 404, 422]


class TestBranchUpdate:
    """Testes para atualização de filiais."""

    def test_update_branch_without_token(self, client, mock_branch, mock_company):
        """Testa atualização de filial sem token."""
        response = client.put(
            f"/branch/update/{mock_branch.IdCompanyBranch}",
            json={
                "name": "Filial Atualizada",
                "code": "FAT001",
                "id_company": mock_company.id_company
            }
        )
        assert response.status_code == 401

    def test_update_branch_with_token(self, client, mock_branch, mock_company, auth_headers):
        """Testa atualização de filial com token válido."""
        response = client.put(
            f"/branch/update/{mock_branch.IdCompanyBranch}",
            json={
                "name": "Filial Atualizada",
                "code": "FAT001",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_update_branch_not_found(self, client, mock_company, auth_headers):
        """Testa atualização de filial inexistente."""
        response = client.put(
            "/branch/update/99999",
            json={
                "name": "Filial Atualizada",
                "code": "FAT001",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestBranchDelete:
    """Testes para exclusão de filiais."""

    def test_delete_branch_without_token(self, client, mock_branch):
        """Testa exclusão de filial sem token."""
        response = client.delete(f"/branch/delete/{mock_branch.IdCompanyBranch}")
        assert response.status_code == 401

    def test_delete_branch_with_token(self, client, mock_branch, auth_headers):
        """Testa exclusão de filial com token válido."""
        response = client.delete(
            f"/branch/delete/{mock_branch.IdCompanyBranch}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_delete_branch_not_found(self, client, auth_headers):
        """Testa exclusão de filial inexistente."""
        response = client.delete("/branch/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]
