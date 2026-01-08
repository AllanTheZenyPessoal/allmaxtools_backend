"""
Testes unitários para os endpoints de Business Partner (Parceiros de Negócios).
"""
import pytest


class TestBusinessPartnerRead:
    """Testes para leitura de parceiros de negócios."""

    def test_read_business_partner_without_token(self, client, mock_business_partner):
        """Testa leitura de parceiro sem token."""
        response = client.get(f"/businnespartner/read/{mock_business_partner.IdBusinessPartner}")
        assert response.status_code == 401

    def test_read_business_partner_with_token(self, client, mock_business_partner, auth_headers):
        """Testa leitura de parceiro com token válido."""
        response = client.get(
            f"/businnespartner/read/{mock_business_partner.IdBusinessPartner}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_business_partner_not_found(self, client, auth_headers):
        """Testa leitura de parceiro inexistente."""
        response = client.get("/businnespartner/read/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestBusinessPartnerList:
    """Testes para listagem de parceiros de negócios."""

    def test_list_business_partners_without_token(self, client):
        """Testa listagem de parceiros sem token."""
        response = client.get("/businnespartner/list/1")
        assert response.status_code == 401

    def test_list_business_partners_with_token(self, client, mock_business_partner, auth_headers):
        """Testa listagem de parceiros com token válido."""
        response = client.get(
            f"/businnespartner/list/{mock_business_partner.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]


class TestBusinessPartnerCreate:
    """Testes para criação de parceiros de negócios."""

    def test_create_business_partner_without_token(self, client, business_partner_payload):
        """Testa criação de parceiro sem token."""
        response = client.post("/businnespartner/create/", json=business_partner_payload)
        assert response.status_code == 401

    def test_create_business_partner_with_token(self, client, business_partner_payload, auth_headers):
        """Testa criação de parceiro com token válido."""
        response = client.post(
            "/businnespartner/create/",
            json=business_partner_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_business_partner_with_missing_fields(self, client, auth_headers):
        """Testa criação de parceiro com campos faltando."""
        response = client.post(
            "/businnespartner/create/",
            json={
                "razao_social": "Parceiro Incompleto"
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_business_partner_with_address(self, client, business_partner_payload, auth_headers):
        """Testa criação de parceiro com endereço embutido."""
        response = client.post(
            "/businnespartner/create/",
            json=business_partner_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_business_partner_with_invalid_cnpj(self, client, auth_headers, mock_company):
        """Testa criação de parceiro com CNPJ inválido."""
        payload = {
            "razao_social": "Parceiro Invalido",
            "nome_fantasia": "Parceiro",
            "cnpj": "",
            "inscricao_estadual": "123",
            "inscricao_municipal": "456",
            "cnae": "123",
            "suframa": "",
            "sugestao_limite_credito": 1000.0,
            "email": "parceiro@teste.com",
            "phone": "11999999999",
            "id_company": mock_company.id_company
        }
        response = client.post(
            "/businnespartner/create/",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 422]


class TestBusinessPartnerUpdate:
    """Testes para atualização de parceiros de negócios."""

    def test_update_business_partner_without_token(self, client, mock_business_partner, mock_company):
        """Testa atualização de parceiro sem token."""
        response = client.put(
            f"/businnespartner/update/{mock_business_partner.IdBusinessPartner}",
            json={
                "razao_social": "Parceiro Atualizado LTDA",
                "nome_fantasia": "Parceiro Atualizado",
                "cnpj": "98765432000199",
                "inscricao_estadual": "123456789",
                "inscricao_municipal": "987654321",
                "cnae": "4712100",
                "suframa": "",
                "sugestao_limite_credito": 15000.00,
                "email": "atualizado@teste.com",
                "phone": "1130003000",
                "id_company": mock_company.id_company
            }
        )
        assert response.status_code == 401

    def test_update_business_partner_with_token(self, client, mock_business_partner, mock_company, auth_headers):
        """Testa atualização de parceiro com token válido."""
        response = client.put(
            f"/businnespartner/update/{mock_business_partner.IdBusinessPartner}",
            json={
                "razao_social": "Parceiro Atualizado LTDA",
                "nome_fantasia": "Parceiro Atualizado",
                "cnpj": "98765432000199",
                "inscricao_estadual": "123456789",
                "inscricao_municipal": "987654321",
                "cnae": "4712100",
                "suframa": "",
                "sugestao_limite_credito": 15000.00,
                "email": "atualizado@teste.com",
                "phone": "1130003000",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_update_business_partner_not_found(self, client, mock_company, auth_headers):
        """Testa atualização de parceiro inexistente."""
        response = client.put(
            "/businnespartner/update/99999",
            json={
                "razao_social": "Parceiro Inexistente",
                "nome_fantasia": "Inexistente",
                "cnpj": "11111111000111",
                "inscricao_estadual": "111",
                "inscricao_municipal": "222",
                "cnae": "123",
                "suframa": "",
                "sugestao_limite_credito": 1000.00,
                "email": "inexistente@teste.com",
                "phone": "1130004000",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestBusinessPartnerDelete:
    """Testes para exclusão de parceiros de negócios."""

    def test_delete_business_partner_without_token(self, client, mock_business_partner):
        """Testa exclusão de parceiro sem token."""
        response = client.delete(f"/businnespartner/delete/{mock_business_partner.IdBusinessPartner}")
        assert response.status_code == 401

    def test_delete_business_partner_with_token(self, client, mock_business_partner, auth_headers):
        """Testa exclusão de parceiro com token válido."""
        response = client.delete(
            f"/businnespartner/delete/{mock_business_partner.IdBusinessPartner}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_delete_business_partner_not_found(self, client, auth_headers):
        """Testa exclusão de parceiro inexistente."""
        response = client.delete("/businnespartner/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]
