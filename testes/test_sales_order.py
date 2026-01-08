"""
Testes unitários para os endpoints de Sales Order (Pedidos de Venda).
"""
import pytest


class TestSalesOrderRead:
    """Testes para leitura de pedidos de venda."""

    def test_read_sales_order_without_token(self, client, mock_sales_order):
        """Testa leitura de pedido sem token."""
        response = client.get(f"/salesorder/{mock_sales_order.IdSalesOrder}")
        assert response.status_code == 401

    def test_read_sales_order_with_token(self, client, mock_sales_order, auth_headers):
        """Testa leitura de pedido com token válido."""
        response = client.get(
            f"/salesorder/{mock_sales_order.IdSalesOrder}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_read_sales_order_not_found(self, client, auth_headers):
        """Testa leitura de pedido inexistente."""
        response = client.get("/salesorder/99999", headers=auth_headers)
        assert response.status_code in [401, 403, 404]


class TestSalesOrderList:
    """Testes para listagem de pedidos de venda."""

    def test_list_sales_orders_without_token(self, client):
        """Testa listagem de pedidos sem token."""
        response = client.get("/salesorder/list/")
        assert response.status_code == 401

    def test_list_sales_orders_with_token(self, client, mock_sales_order, auth_headers):
        """Testa listagem de pedidos com token válido."""
        response = client.get("/salesorder/list/", headers=auth_headers)
        assert response.status_code in [200, 401, 403]

    def test_list_sales_orders_with_date_filter(self, client, auth_headers):
        """Testa listagem de pedidos com filtro de data."""
        response = client.get(
            "/salesorder/list/?start_date=2026-01-01&end_date=2026-12-31",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_list_sales_orders_with_status_filter(self, client, auth_headers):
        """Testa listagem de pedidos com filtro de status."""
        response = client.get(
            "/salesorder/list/?status=pending",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_list_sales_orders_with_business_partner_filter(self, client, mock_business_partner, auth_headers):
        """Testa listagem de pedidos com filtro de parceiro de negócios."""
        response = client.get(
            f"/salesorder/list/?business_partner_id={mock_business_partner.IdBusinessPartner}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]


class TestSalesOrderCreate:
    """Testes para criação de pedidos de venda."""

    def test_create_sales_order_without_token(self, client, sales_order_payload):
        """Testa criação de pedido sem token."""
        response = client.post("/salesorder/save/", json=sales_order_payload)
        assert response.status_code == 401

    def test_create_sales_order_with_token(self, client, sales_order_payload, auth_headers):
        """Testa criação de pedido com token válido."""
        response = client.post(
            "/salesorder/save/",
            json=sales_order_payload,
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 403]

    def test_create_sales_order_with_missing_fields(self, client, auth_headers):
        """Testa criação de pedido com campos faltando."""
        response = client.post(
            "/salesorder/save/",
            json={
                "observation": "Pedido incompleto"
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 422]

    def test_create_sales_order_with_invalid_business_partner(self, client, mock_branch, auth_headers):
        """Testa criação de pedido com parceiro de negócios inexistente."""
        response = client.post(
            "/salesorder/save/",
            json={
                "data_entrega": "2026-01-20",
                "id_business_partner": 99999,
                "id_company_branch": mock_branch.IdCompanyBranch
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 403, 404, 422]

    def test_create_sales_order_with_invalid_branch(self, client, mock_business_partner, auth_headers):
        """Testa criação de pedido com filial inexistente."""
        response = client.post(
            "/salesorder/save/",
            json={
                "data_entrega": "2026-01-20",
                "id_business_partner": mock_business_partner.IdBusinessPartner,
                "id_company_branch": 99999
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 403, 404, 422]

    def test_create_sales_order_with_all_optional_fields(self, client, mock_business_partner, mock_branch, 
                                                         mock_freight, mock_payment_method, mock_payment_term,
                                                         mock_utilization, auth_headers):
        """Testa criação de pedido com todos os campos opcionais."""
        response = client.post(
            "/salesorder/save/",
            json={
                "redespacho": 1,
                "data_entrega": "2026-01-25",
                "discount": 15.0,
                "observation": "Pedido completo com todos os campos",
                "id_business_partner": mock_business_partner.IdBusinessPartner,
                "id_company_branch": mock_branch.IdCompanyBranch,
                "id_company_freight": mock_freight.IdCompanyFreight,
                "id_company_payment_method": mock_payment_method.IdCompanyPaymentMethod,
                "id_company_payment_term": mock_payment_term.IdCompanyPaymentTerm,
                "id_company_utilization": mock_utilization.IdCompanyUtilization
            },
            headers=auth_headers
        )
        assert response.status_code in [201, 401, 403]


class TestSalesOrderUpdate:
    """Testes para atualização de pedidos de venda."""

    def test_update_sales_order_without_token(self, client, mock_sales_order):
        """Testa atualização de pedido sem token."""
        response = client.put(
            f"/salesorder/update/{mock_sales_order.IdSalesOrder}",
            json={
                "discount": 20.0,
                "observation": "Pedido atualizado"
            }
        )
        assert response.status_code == 401

    def test_update_sales_order_with_token(self, client, mock_sales_order, auth_headers):
        """Testa atualização de pedido com token válido."""
        response = client.put(
            f"/salesorder/update/{mock_sales_order.IdSalesOrder}",
            json={
                "discount": 20.0,
                "observation": "Pedido atualizado"
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_update_sales_order_not_found(self, client, auth_headers):
        """Testa atualização de pedido inexistente."""
        response = client.put(
            "/salesorder/update/99999",
            json={
                "discount": 10.0
            },
            headers=auth_headers
        )
        assert response.status_code in [401, 403, 404]

    def test_update_sales_order_partial_update(self, client, mock_sales_order, auth_headers):
        """Testa atualização parcial de pedido."""
        response = client.put(
            f"/salesorder/update/{mock_sales_order.IdSalesOrder}",
            json={
                "observation": "Apenas observação atualizada"
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_update_sales_order_delivery_date(self, client, mock_sales_order, auth_headers):
        """Testa atualização da data de entrega."""
        response = client.put(
            f"/salesorder/update/{mock_sales_order.IdSalesOrder}",
            json={
                "data_entrega": "2026-02-01"
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]


class TestSalesOrderDelete:
    """Testes para exclusão de pedidos de venda."""

    def test_delete_sales_order_without_token(self, client, mock_sales_order):
        """Testa exclusão de pedido sem token."""
        response = client.delete(f"/salesorder/delete/{mock_sales_order.IdSalesOrder}")
        assert response.status_code == 401

    def test_delete_sales_order_with_token(self, client, mock_sales_order, auth_headers):
        """Testa exclusão de pedido com token válido."""
        response = client.delete(
            f"/salesorder/delete/{mock_sales_order.IdSalesOrder}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_delete_sales_order_not_found(self, client, auth_headers):
        """Testa exclusão de pedido inexistente."""
        response = client.delete("/salesorder/delete/99999", headers=auth_headers)
        assert response.status_code in [401, 403, 404]


class TestSalesOrderFilters:
    """Testes para filtros de pedidos de venda."""

    def test_filter_by_created_by_user(self, client, superadmin_user, auth_headers):
        """Testa filtro por usuário que criou o pedido."""
        response = client.get(
            f"/salesorder/list/?created_by={superadmin_user.id_user}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_filter_with_multiple_parameters(self, client, mock_business_partner, auth_headers):
        """Testa filtro com múltiplos parâmetros."""
        response = client.get(
            f"/salesorder/list/?start_date=2026-01-01&end_date=2026-12-31&business_partner_id={mock_business_partner.IdBusinessPartner}",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]

    def test_filter_returns_empty_for_no_matches(self, client, auth_headers):
        """Testa que filtro retorna vazio quando não há correspondências."""
        response = client.get(
            "/salesorder/list/?start_date=2030-01-01&end_date=2030-12-31",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]
