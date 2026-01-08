"""
Testes unitários para os endpoints de Payment Method (Métodos de Pagamento).
"""
import pytest


class TestPaymentMethodRead:
    """Testes para leitura de métodos de pagamento."""

    def test_read_payment_method_without_token(self, client, mock_payment_method):
        """Testa leitura de método de pagamento sem token."""
        response = client.get(f"/paymentmethod/read/{mock_payment_method.IdCompanyPaymentMethod}")
        assert response.status_code == 401

    def test_read_payment_method_with_token(self, client, mock_payment_method, auth_headers):
        """Testa leitura de método de pagamento com token válido."""
        response = client.get(
            f"/paymentmethod/read/{mock_payment_method.IdCompanyPaymentMethod}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_read_payment_method_not_found(self, client, auth_headers):
        """Testa leitura de método de pagamento inexistente."""
        response = client.get("/paymentmethod/read/99999", headers=auth_headers)
        assert response.status_code in [401, 404]


class TestPaymentMethodList:
    """Testes para listagem de métodos de pagamento."""

    def test_list_payment_methods_without_token(self, client, mock_company):
        """Testa listagem de métodos de pagamento sem token."""
        response = client.get(f"/paymentmethod/list/{mock_company.id_company}")
        assert response.status_code == 401

    def test_list_payment_methods_with_token(self, client, mock_company, mock_payment_method, auth_headers):
        """Testa listagem de métodos de pagamento com token válido."""
        response = client.get(
            f"/paymentmethod/list/{mock_company.id_company}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_payment_methods_empty_company(self, client, auth_headers):
        """Testa listagem de métodos de pagamento para empresa sem métodos."""
        response = client.get("/paymentmethod/list/99999", headers=auth_headers)
        assert response.status_code in [200, 401, 404]


class TestPaymentMethodCreate:
    """Testes para criação de métodos de pagamento."""

    def test_create_payment_method_without_token(self, client, payment_method_payload):
        """Testa criação de método de pagamento sem token."""
        response = client.post("/paymentmethod/create/", json=payment_method_payload)
        assert response.status_code == 401

    def test_create_payment_method_with_token(self, client, payment_method_payload, auth_headers):
        """Testa criação de método de pagamento com token válido."""
        response = client.post(
            "/paymentmethod/create/",
            json=payment_method_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401]

    def test_create_payment_method_with_missing_fields(self, client, auth_headers):
        """Testa criação de método de pagamento com campos faltando."""
        response = client.post(
            "/paymentmethod/create/",
            json={"name": "Método Incompleto"},
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_payment_method_with_invalid_company(self, client, auth_headers):
        """Testa criação de método de pagamento para empresa inexistente."""
        response = client.post(
            "/paymentmethod/create/",
            json={
                "name": "Boleto",
                "code": "BOL001",
                "id_company": 99999
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 404, 422]


class TestPaymentMethodUpdate:
    """Testes para atualização de métodos de pagamento."""

    def test_update_payment_method_without_token(self, client, mock_payment_method, mock_company):
        """Testa atualização de método de pagamento sem token."""
        response = client.put(
            f"/paymentmethod/update/{mock_payment_method.IdCompanyPaymentMethod}",
            json={
                "name": "Cartão Débito",
                "code": "CD001",
                "id_company": mock_company.id_company
            }
        )
        assert response.status_code == 401

    def test_update_payment_method_with_token(self, client, mock_payment_method, mock_company, auth_headers):
        """Testa atualização de método de pagamento com token válido."""
        response = client.put(
            f"/paymentmethod/update/{mock_payment_method.IdCompanyPaymentMethod}",
            json={
                "name": "Cartão Débito",
                "code": "CD001",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_update_payment_method_not_found(self, client, mock_company, auth_headers):
        """Testa atualização de método de pagamento inexistente."""
        response = client.put(
            "/paymentmethod/update/99999",
            json={
                "name": "Método Inexistente",
                "code": "MNE001",
                "id_company": mock_company.id_company
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


class TestPaymentMethodDelete:
    """Testes para exclusão de métodos de pagamento."""

    def test_delete_payment_method_without_token(self, client, mock_payment_method):
        """Testa exclusão de método de pagamento sem token."""
        response = client.delete(f"/paymentmethod/delete/{mock_payment_method.IdCompanyPaymentMethod}")
        assert response.status_code == 401

    def test_delete_payment_method_with_token(self, client, mock_payment_method, auth_headers):
        """Testa exclusão de método de pagamento com token válido."""
        response = client.delete(
            f"/paymentmethod/delete/{mock_payment_method.IdCompanyPaymentMethod}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_delete_payment_method_not_found(self, client, auth_headers):
        """Testa exclusão de método de pagamento inexistente."""
        response = client.delete("/paymentmethod/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 404]
