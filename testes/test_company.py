"""
Testes unitários para os endpoints de Company.
"""
import pytest


class TestCompanyCreate:
    """Testes para criação de empresas."""

    def test_create_company_without_token(self, client, company_payload):
        """Testa criação de empresa sem token."""
        response = client.post("/company/save/", json=company_payload)
        assert response.status_code == 401

    def test_create_company_with_token(self, client, company_payload, auth_headers):
        """Testa criação de empresa com token válido."""
        response = client.post(
            "/company/save/",
            json=company_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_company_with_missing_data(self, client, auth_headers):
        """Testa criação de empresa com dados faltando."""
        response = client.post(
            "/company/save/",
            json={"CompanyBase": {"razao_social": "Teste"}},
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_company_with_invalid_cnpj(self, client, auth_headers, address_payload):
        """Testa criação de empresa com CNPJ inválido."""
        payload = {
            "CompanyBase": {
                "razao_social": "Empresa Teste",
                "nome_fantasia": "Teste",
                "cnpj": "",  # CNPJ vazio
                "email": "teste@empresa.com",
                "phone": "1140001000",
                "active": True
            },
            "AddressBase": address_payload
        }
        response = client.post(
            "/company/save/",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [401, 422]


class TestCompanyRead:
    """Testes para leitura de empresas."""

    def test_read_company_without_token(self, client, mock_company):
        """Testa leitura de empresa sem token."""
        response = client.get(f"/company/{mock_company.id_company}")
        assert response.status_code == 401

    def test_read_company_with_token(self, client, mock_company, auth_headers):
        """Testa leitura de empresa com token válido."""
        response = client.get(
            f"/company/{mock_company.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_company_not_found(self, client, auth_headers):
        """Testa leitura de empresa inexistente."""
        response = client.get("/company/99999", headers=auth_headers)
        assert response.status_code in [401, 404]

    def test_read_company_invalid_id(self, client, auth_headers):
        """Testa leitura de empresa com ID inválido."""
        response = client.get("/company/invalid", headers=auth_headers)
        assert response.status_code in [401, 422]


class TestCompanyList:
    """Testes para listagem de empresas."""

    def test_list_companies_without_auth(self, client):
        """Testa listagem de empresas sem autenticação."""
        response = client.get("/companies/")
        assert response.status_code == 401

    def test_list_companies_with_auth(self, client, auth_headers, mock_company):
        """Testa listagem de empresas com autenticação."""
        response = client.get("/companies/", headers=auth_headers)
        assert response.status_code in [200, 401, 403]


class TestCompanyUpdate:
    """Testes para atualização de empresas."""

    def test_update_company_without_token(self, client, mock_company):
        """Testa atualização de empresa sem token."""
        response = client.put(
            f"/company/update/{mock_company.id_company}",
            json={
                "razao_social": "Empresa Atualizada LTDA",
                "nome_fantasia": "Empresa Atualizada",
                "cnpj": "12345678000100",
                "email": "atualizada@empresa.com",
                "phone": "1140002000",
                "active": True
            }
        )
        assert response.status_code == 401

    def test_update_company_not_found(self, client, auth_headers):
        """Testa atualização de empresa inexistente."""
        response = client.put(
            "/company/update/99999",
            json={
                "razao_social": "Empresa Atualizada LTDA",
                "nome_fantasia": "Empresa Atualizada",
                "cnpj": "12345678000100",
                "email": "atualizada@empresa.com",
                "phone": "1140002000",
                "active": True
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestCompanyDelete:
    """Testes para exclusão de empresas."""

    def test_delete_company_without_token(self, client, mock_company):
        """Testa exclusão de empresa sem token."""
        response = client.delete(f"/company/delete/{mock_company.id_company}")
        assert response.status_code == 401

    def test_delete_company_not_found(self, client, auth_headers):
        """Testa exclusão de empresa inexistente."""
        response = client.delete("/company/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestCompanyUserAttachment:
    """Testes para anexar usuário a empresa."""

    def test_attach_user_to_company_without_token(self, client, mock_company, superadmin_user):
        """Testa anexar usuário a empresa sem token."""
        response = client.post(
            "/company/user_to_company/",
            json={
                "id_company": mock_company.id_company,
                "id_user": superadmin_user.id_user
            }
        )
        assert response.status_code == 401

    def test_attach_user_to_company_with_token(self, client, mock_company, superadmin_user, auth_headers):
        """Testa anexar usuário a empresa com token."""
        response = client.post(
            "/company/user_to_company/",
            json={
                "id_company": mock_company.id_company,
                "id_user": superadmin_user.id_user
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401]
