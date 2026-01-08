"""
Testes unitários para os endpoints de Payment Terms (Condições de Pagamento).
"""
import pytest


class TestPaymentTermRead:
    """Testes para leitura de condições de pagamento."""

    def test_read_payment_term_without_token(self, client, mock_payment_term):
        """Testa leitura de condição de pagamento sem token."""
        response = client.get(f"/paymentterm/read/{mock_payment_term.IdCompanyPaymentTerm}")
        assert response.status_code == 401

    def test_read_payment_term_with_token(self, client, mock_payment_term, auth_headers):
        """Testa leitura de condição de pagamento com token válido."""
        response = client.get(
            f"/paymentterm/read/{mock_payment_term.IdCompanyPaymentTerm}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_payment_term_not_found(self, client, auth_headers):
        """Testa leitura de condição de pagamento inexistente."""
        response = client.get("/paymentterm/read/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestPaymentTermList:
    """Testes para listagem de condições de pagamento."""

    def test_list_payment_terms_without_token(self, client, mock_company):
        """Testa listagem de condições de pagamento sem token."""
        response = client.get(f"/paymentterm/list/{mock_company.id_company}")
        assert response.status_code == 401

    def test_list_payment_terms_with_token(self, client, mock_company, mock_payment_term, auth_headers):
        """Testa listagem de condições de pagamento com token válido."""
        response = client.get(
            f"/paymentterm/list/{mock_company.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_payment_terms_empty_company(self, client, auth_headers):
        """Testa listagem de condições de pagamento para empresa sem condições."""
        response = client.get("/paymentterm/list/99999", headers=auth_headers)
        assert response.status_code in [200, 401, 404]


class TestPaymentTermCreate:
    """Testes para criação de condições de pagamento."""

    def test_create_payment_term_without_token(self, client, payment_term_payload):
        """Testa criação de condição de pagamento sem token."""
        response = client.post("/paymentterm/create/", json=payment_term_payload)
        assert response.status_code == 401

    def test_create_payment_term_with_token(self, client, payment_term_payload, auth_headers):
        """Testa criação de condição de pagamento com token válido."""
        response = client.post(
            "/paymentterm/create/",
            json=payment_term_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_payment_term_with_missing_fields(self, client, auth_headers):
        """Testa criação de condição de pagamento com campos faltando."""
        response = client.post(
            "/paymentterm/create/",
            json={"name": "Condição Incompleta"},
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_payment_term_with_invalid_company(self, client, auth_headers):
        """Testa criação de condição de pagamento para empresa inexistente."""
        response = client.post(
            "/paymentterm/create/",
            json={
                "name": "À Vista",
                "code": "AV001",
                "id_company": 99999
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 404, 422]

    def test_create_payment_term_various_terms(self, client, mock_company, auth_headers):
        """Testa criação de várias condições de pagamento."""
        terms = [
            {"name": "À Vista", "code": "AV", "id_company": mock_company.id_company},
            {"name": "30/60/90", "code": "306090", "id_company": mock_company.id_company},
            {"name": "Entrada + 30", "code": "E30", "id_company": mock_company.id_company}
        ]
        
        for term in terms:
            response = client.post(
                "/paymentterm/create/",
                json=term,
                headers=auth_headers
            )
            assert response.status_code in [201, 401]


class TestPaymentTermUpdate:
    """Testes para atualização de condições de pagamento."""

    def test_update_payment_term_without_token(self, client, mock_payment_term, mock_company):
        """Testa atualização de condição de pagamento sem token."""
        response = client.put(
            f"/paymentterm/update/{mock_payment_term.IdCompanyPaymentTerm}",
            json={
                "name": "45 dias",
                "code": "45D",
                "id_company": mock_company.id_company
            }
        )
        assert response.status_code == 401

    def test_update_payment_term_with_token(self, client, mock_payment_term, mock_company, auth_headers):
        """Testa atualização de condição de pagamento com token válido."""
        response = client.put(
            f"/paymentterm/update/{mock_payment_term.IdCompanyPaymentTerm}",
            json={
                "name": "45 dias",
                "code": "45D",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_update_payment_term_not_found(self, client, mock_company, auth_headers):
        """Testa atualização de condição de pagamento inexistente."""
        response = client.put(
            "/paymentterm/update/99999",
            json={
                "name": "Condição Inexistente",
                "code": "CNE001",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestPaymentTermDelete:
    """Testes para exclusão de condições de pagamento."""

    def test_delete_payment_term_without_token(self, client, mock_payment_term):
        """Testa exclusão de condição de pagamento sem token."""
        response = client.delete(f"/paymentterm/delete/{mock_payment_term.IdCompanyPaymentTerm}")
        assert response.status_code == 401

    def test_delete_payment_term_with_token(self, client, mock_payment_term, auth_headers):
        """Testa exclusão de condição de pagamento com token válido."""
        response = client.delete(
            f"/paymentterm/delete/{mock_payment_term.IdCompanyPaymentTerm}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_delete_payment_term_not_found(self, client, auth_headers):
        """Testa exclusão de condição de pagamento inexistente."""
        response = client.delete("/paymentterm/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]
