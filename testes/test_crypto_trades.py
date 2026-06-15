"""Testes de validação de wallet para operações de compra e venda de criptomoedas.

Cobre:
- Compra com saldo USD suficiente (deve passar)
- Compra com saldo USD insuficiente (deve rejeitar com 400)
- Venda com quantidade de cripto suficiente (deve passar)
- Venda com quantidade de cripto insuficiente (deve rejeitar com 400)
- Venda com holding zerado / não existente (deve rejeitar com 400)
- Compra seguida de venda atualiza saldos corretamente
"""

import pytest
from database import db_models # type: ignore
from endpoint.user import get_password_hash # type: ignore
from token_utils.apikey_generator import create_access_token # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, *, email="trader@test.com", username="trader"):
    user = db_models.User(
        username=username,
        email=email,
        password=get_password_hash("secret123"),
        role="user",
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(user):
    token, _ = create_access_token(
        email=user.email,
        username=user.username,
        id_user=user.id_user,
        role=user.role,
        company_id=user.company_id,
    )
    return token


def _fund_account(db, user_id, balance_usdt):
    account = db_models.UserAccount(user_id=user_id, balance_usdt=balance_usdt)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _fund_holding(db, user_id, symbol, quantity):
    holding = db_models.UserHolding(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity,
        avg_cost_usdt=50000.0,
        current_value_usdt=quantity * 50000.0,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Testes de COMPRA (buy)
# ---------------------------------------------------------------------------

class TestBuyWalletValidation:
    def test_buy_with_sufficient_balance_succeeds(self, client, test_db):
        """Compra deve ser executada quando saldo USD é suficiente."""
        user = _create_user(test_db)
        _fund_account(test_db, user.id_user, balance_usdt=10_000.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["trade_type"] == "buy"
        assert data["symbol"] == "BTC"
        assert data["quantity"] == 0.1
        # Saldo restante deve refletir o débito
        assert data["balance_usdt"] == pytest.approx(10_000.0 - 5_000.0, abs=0.01)

    def test_buy_with_exact_balance_succeeds(self, client, test_db):
        """Compra com saldo exatamente igual ao total deve passar."""
        user = _create_user(test_db, email="exact@test.com", username="exact")
        _fund_account(test_db, user.id_user, balance_usdt=5_000.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 200, response.text

    def test_buy_with_insufficient_balance_returns_400(self, client, test_db):
        """Compra deve ser rejeitada quando saldo USD é insuficiente."""
        user = _create_user(test_db, email="broke@test.com", username="broke")
        _fund_account(test_db, user.id_user, balance_usdt=100.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "saldo insuficiente" in detail.lower()
        assert "100.00" in detail  # mostra o saldo disponível
        assert "50000.00" in detail  # mostra o valor necessário

    def test_buy_with_zero_balance_returns_400(self, client, test_db):
        """Compra deve ser rejeitada quando saldo USD é zero."""
        user = _create_user(test_db, email="zero@test.com", username="zero")
        _fund_account(test_db, user.id_user, balance_usdt=0.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/buy",
            json={"symbol": "ETH", "quantity": 0.5, "unit_price_usdt": 3_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 400
        assert "saldo insuficiente" in response.json()["detail"].lower()

    def test_buy_without_account_creates_account_and_rejects_when_no_balance(self, client, test_db):
        """Usuário sem conta criada inicia com saldo zero e deve ser rejeitado."""
        user = _create_user(test_db, email="noaccount@test.com", username="noaccount")
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.01, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 400
        assert "saldo insuficiente" in response.json()["detail"].lower()

    def test_buy_does_not_debit_balance_when_rejected(self, client, test_db):
        """Saldo não deve ser alterado quando a compra é rejeitada."""
        user = _create_user(test_db, email="nodebit@test.com", username="nodebit")
        _fund_account(test_db, user.id_user, balance_usdt=200.0)
        token = _make_token(user)

        # Tentativa rejeitada
        client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        # Verificar que o saldo não foi alterado
        account = (
            test_db.query(db_models.UserAccount)
            .filter(db_models.UserAccount.user_id == user.id_user)
            .first()
        )
        assert account.balance_usdt == pytest.approx(200.0, abs=0.01)


# ---------------------------------------------------------------------------
# Testes de VENDA (sell)
# ---------------------------------------------------------------------------

class TestSellWalletValidation:
    def test_sell_with_sufficient_holding_succeeds(self, client, test_db):
        """Venda deve ser executada quando quantidade de cripto é suficiente."""
        user = _create_user(test_db, email="seller@test.com", username="seller")
        _fund_account(test_db, user.id_user, balance_usdt=0.0)
        _fund_holding(test_db, user.id_user, "BTC", quantity=1.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/sell",
            json={"symbol": "BTC", "quantity": 0.5, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["trade_type"] == "sell"
        assert data["holding_quantity"] == pytest.approx(0.5, abs=1e-8)
        # Saldo USD deve ter sido creditado
        assert data["balance_usdt"] == pytest.approx(25_000.0, abs=0.01)

    def test_sell_exact_quantity_succeeds(self, client, test_db):
        """Venda de quantidade exatamente igual ao holding deve passar."""
        user = _create_user(test_db, email="sellexact@test.com", username="sellexact")
        _fund_account(test_db, user.id_user, balance_usdt=0.0)
        _fund_holding(test_db, user.id_user, "ETH", quantity=2.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/sell",
            json={"symbol": "ETH", "quantity": 2.0, "unit_price_usdt": 3_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 200, response.text
        assert response.json()["holding_quantity"] == pytest.approx(0.0, abs=1e-8)

    def test_sell_with_insufficient_holding_returns_400(self, client, test_db):
        """Venda deve ser rejeitada quando quantidade de cripto é insuficiente."""
        user = _create_user(test_db, email="nocoins@test.com", username="nocoins")
        _fund_account(test_db, user.id_user, balance_usdt=100_000.0)
        _fund_holding(test_db, user.id_user, "BTC", quantity=0.1)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/sell",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "saldo insuficiente" in detail.lower()
        assert "btc" in detail.lower()
        assert "0.10000000" in detail  # quantidade disponível
        assert "1.00000000" in detail  # quantidade necessária

    def test_sell_without_holding_returns_400(self, client, test_db):
        """Venda de moeda sem holding registrado deve ser rejeitada."""
        user = _create_user(test_db, email="noholding@test.com", username="noholding")
        _fund_account(test_db, user.id_user, balance_usdt=100_000.0)
        token = _make_token(user)

        response = client.post(
            "/crypto/trades/sell",
            json={"symbol": "ETH", "quantity": 1.0, "unit_price_usdt": 3_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 400
        assert "saldo insuficiente" in response.json()["detail"].lower()

    def test_sell_does_not_credit_balance_when_rejected(self, client, test_db):
        """Saldo USD não deve ser creditado quando a venda é rejeitada."""
        user = _create_user(test_db, email="nocredit@test.com", username="nocredit")
        _fund_account(test_db, user.id_user, balance_usdt=500.0)
        _fund_holding(test_db, user.id_user, "BTC", quantity=0.01)
        token = _make_token(user)

        # Tentativa rejeitada
        client.post(
            "/crypto/trades/sell",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        account = (
            test_db.query(db_models.UserAccount)
            .filter(db_models.UserAccount.user_id == user.id_user)
            .first()
        )
        assert account.balance_usdt == pytest.approx(500.0, abs=0.01)


# ---------------------------------------------------------------------------
# Testes de fluxo completo (buy → sell)
# ---------------------------------------------------------------------------

class TestBuySellFlow:
    def test_buy_then_sell_updates_balances_correctly(self, client, test_db):
        """Fluxo completo: compra BTC com USD, depois vende e recupera USD."""
        user = _create_user(test_db, email="fullflow@test.com", username="fullflow")
        _fund_account(test_db, user.id_user, balance_usdt=100_000.0)
        token = _make_token(user)

        # Compra 1 BTC a 50.000 USD
        buy_resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert buy_resp.status_code == 200
        assert buy_resp.json()["balance_usdt"] == pytest.approx(50_000.0, abs=0.01)
        assert buy_resp.json()["holding_quantity"] == pytest.approx(1.0, abs=1e-8)

        # Vende 1 BTC a 55.000 USD (lucro)
        sell_resp = client.post(
            "/crypto/trades/sell",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 55_000.0},
            headers=_auth(token),
        )
        assert sell_resp.status_code == 200
        assert sell_resp.json()["balance_usdt"] == pytest.approx(105_000.0, abs=0.01)
        assert sell_resp.json()["holding_quantity"] == pytest.approx(0.0, abs=1e-8)

    def test_cannot_sell_after_balance_depleted_by_buy(self, client, test_db):
        """Após comprar todo o saldo disponível, nova venda de moeda inexistente falha."""
        user = _create_user(test_db, email="deplete@test.com", username="deplete")
        _fund_account(test_db, user.id_user, balance_usdt=3_000.0)
        token = _make_token(user)

        # Compra 1 ETH a 3.000 USD — esgota o saldo
        buy_resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "ETH", "quantity": 1.0, "unit_price_usdt": 3_000.0},
            headers=_auth(token),
        )
        assert buy_resp.status_code == 200
        assert buy_resp.json()["balance_usdt"] == pytest.approx(0.0, abs=0.01)

        # Tenta comprar de novo sem saldo
        second_buy = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.01, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert second_buy.status_code == 400
        assert "saldo insuficiente" in second_buy.json()["detail"].lower()

    def test_unauthenticated_buy_returns_401(self, client, test_db):
        """Compra sem token deve ser rejeitada com 401/403."""
        response = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
        )
        assert response.status_code in (401, 403)

    def test_unauthenticated_sell_returns_401(self, client, test_db):
        """Venda sem token deve ser rejeitada com 401/403."""
        response = client.post(
            "/crypto/trades/sell",
            json={"symbol": "ETH", "quantity": 0.5, "unit_price_usdt": 3_000.0},
        )
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Paper-mode helpers
# ---------------------------------------------------------------------------

def _make_paper_token(user):
    token, _ = create_access_token(
        email=user.email,
        username=user.username,
        id_user=user.id_user,
        role=user.role,
        company_id=user.company_id,
        trade_mode="paper",
    )
    return token


def _fund_paper_account(db, user_id, balance_usdt):
    account = db_models.PaperBalance(user_id=user_id, balance_usdt=balance_usdt)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _fund_paper_holding(db, user_id, symbol, quantity):
    holding = db_models.PaperHolding(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity,
        avg_cost_usdt=50_000.0,
        current_value_usdt=quantity * 50_000.0,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


# ---------------------------------------------------------------------------
# Paper-mode segregation tests
# ---------------------------------------------------------------------------

class TestPaperMode:
    def test_paper_buy_with_funded_paper_balance_succeeds(self, client, test_db):
        """Paper buy debits paper balance and records trade_mode=paper."""
        user = _create_user(test_db, email="paperbuy@test.com", username="paperbuy")
        _fund_paper_account(test_db, user.id_user, balance_usdt=10_000.0)
        token = _make_paper_token(user)

        response = client.post(
            "/crypto/trades/buy?mode=paper",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["trade_mode"] == "paper"
        assert data["balance_usdt"] == pytest.approx(5_000.0, abs=0.01)

    def test_paper_sell_credits_paper_balance(self, client, test_db):
        """Paper sell credits paper balance and decrements paper holding."""
        user = _create_user(test_db, email="papersell@test.com", username="papersell")
        _fund_paper_account(test_db, user.id_user, balance_usdt=0.0)
        _fund_paper_holding(test_db, user.id_user, "BTC", quantity=1.0)
        token = _make_paper_token(user)

        response = client.post(
            "/crypto/trades/sell?mode=paper",
            json={"symbol": "BTC", "quantity": 0.5, "unit_price_usdt": 60_000.0},
            headers=_auth(token),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["trade_mode"] == "paper"
        assert data["balance_usdt"] == pytest.approx(30_000.0, abs=0.01)
        assert data["holding_quantity"] == pytest.approx(0.5, abs=1e-8)

    def test_paper_buy_does_not_affect_live_balance(self, client, test_db):
        """Paper trades must not touch the live UserAccount."""
        user = _create_user(test_db, email="isolate@test.com", username="isolate")
        _fund_paper_account(test_db, user.id_user, balance_usdt=100_000.0)
        _fund_account(test_db, user.id_user, balance_usdt=50_000.0)
        paper_token = _make_paper_token(user)

        client.post(
            "/crypto/trades/buy?mode=paper",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(paper_token),
        )

        live_account = (
            test_db.query(db_models.UserAccount)
            .filter(db_models.UserAccount.user_id == user.id_user)
            .first()
        )
        assert live_account is not None
        assert live_account.balance_usdt == pytest.approx(50_000.0, abs=0.01)

    def test_paper_buy_does_not_create_live_holding(self, client, test_db):
        """Paper buy must not create a UserHolding row."""
        user = _create_user(test_db, email="nolive@test.com", username="nolive")
        _fund_paper_account(test_db, user.id_user, balance_usdt=100_000.0)
        paper_token = _make_paper_token(user)

        client.post(
            "/crypto/trades/buy?mode=paper",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(paper_token),
        )

        live_holding = (
            test_db.query(db_models.UserHolding)
            .filter(db_models.UserHolding.user_id == user.id_user)
            .first()
        )
        assert live_holding is None

    def test_live_token_rejected_for_paper_mode(self, client, test_db):
        """A live-bound token must be rejected when the request targets paper mode."""
        user = _create_user(test_db, email="mismatch1@test.com", username="mismatch1")
        live_token = _make_token(user)

        response = client.post(
            "/crypto/trades/buy?mode=paper",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(live_token),
        )

        assert response.status_code == 403

    def test_paper_token_rejected_for_live_mode(self, client, test_db):
        """A paper-bound token must be rejected when the request targets live mode."""
        user = _create_user(test_db, email="mismatch2@test.com", username="mismatch2")
        paper_token = _make_paper_token(user)

        response = client.post(
            "/crypto/trades/buy?mode=live",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(paper_token),
        )

        assert response.status_code == 403

    def test_paper_insufficient_balance_returns_400(self, client, test_db):
        """Paper buy with no paper balance is rejected with 400."""
        user = _create_user(test_db, email="paperbroke@test.com", username="paperbroke")
        _fund_paper_account(test_db, user.id_user, balance_usdt=10.0)
        paper_token = _make_paper_token(user)

        response = client.post(
            "/crypto/trades/buy?mode=paper",
            json={"symbol": "BTC", "quantity": 1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(paper_token),
        )

        assert response.status_code == 400
        assert "saldo insuficiente" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Edge-case validation tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def _user_with_account(self, db, email, username, balance=10_000.0):
        user = _create_user(db, email=email, username=username)
        _fund_account(db, user.id_user, balance_usdt=balance)
        return user

    def test_buy_zero_quantity_returns_400(self, client, test_db):
        user = self._user_with_account(test_db, "zero_qty@test.com", "zero_qty")
        token = _make_token(user)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_buy_negative_quantity_returns_400(self, client, test_db):
        user = self._user_with_account(test_db, "neg_qty@test.com", "neg_qty")
        token = _make_token(user)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": -1.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_buy_negative_price_returns_400(self, client, test_db):
        user = self._user_with_account(test_db, "neg_price@test.com", "neg_price")
        token = _make_token(user)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": -1.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_buy_below_minimum_quantity_returns_400(self, client, test_db):
        """BTC minimum is 0.0001 — submitting 0.00001 must be rejected."""
        user = self._user_with_account(test_db, "btc_min@test.com", "btc_min", balance=10_000_000.0)
        token = _make_token(user)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.00001, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "minimum" in resp.json()["detail"].lower()

    def test_buy_above_maximum_quantity_returns_400(self, client, test_db):
        """BTC maximum is 100 — submitting 101 must be rejected."""
        user = self._user_with_account(test_db, "btc_max@test.com", "btc_max", balance=100_000_000.0)
        token = _make_token(user)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 101.0, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "maximum" in resp.json()["detail"].lower()

    def test_buy_eth_below_minimum_returns_400(self, client, test_db):
        """ETH minimum is 0.001."""
        user = self._user_with_account(test_db, "eth_min@test.com", "eth_min")
        token = _make_token(user)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "ETH", "quantity": 0.0001, "unit_price_usdt": 3_000.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Price deviation tests
# ---------------------------------------------------------------------------

class TestLivePriceValidation:
    def test_price_within_tolerance_passes(self, client, test_db):
        """0.5% deviation is within the 1% threshold — order must succeed."""
        user = _create_user(test_db, email="within_tol@test.com", username="within_tol")
        _fund_account(test_db, user.id_user, balance_usdt=100_000.0)
        token = _make_token(user)

        snapshot = db_models.CryptoPriceSnapshot(
            symbol="BTC", pair="BTCUSDT", price_usdt=50_000.0, source="test",
        )
        test_db.add(snapshot)
        test_db.commit()

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_250.0},  # +0.5%
            headers=_auth(token),
        )
        assert resp.status_code == 200

    def test_price_above_tolerance_returns_400(self, client, test_db):
        """2% deviation exceeds 1% threshold — order must be rejected."""
        user = _create_user(test_db, email="above_tol@test.com", username="above_tol")
        _fund_account(test_db, user.id_user, balance_usdt=100_000.0)
        token = _make_token(user)

        snapshot = db_models.CryptoPriceSnapshot(
            symbol="BTC", pair="BTCUSDT", price_usdt=50_000.0, source="test",
        )
        test_db.add(snapshot)
        test_db.commit()

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 51_100.0},  # +2.2%
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "price deviation" in resp.json()["detail"].lower()

    def test_no_snapshot_skips_price_check(self, client, test_db):
        """When no price snapshot exists, the check is skipped and the order proceeds."""
        user = _create_user(test_db, email="no_snap@test.com", username="no_snap")
        _fund_account(test_db, user.id_user, balance_usdt=100_000.0)
        token = _make_token(user)

        # No snapshot inserted
        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.001, "unit_price_usdt": 99_000.0},
            headers=_auth(token),
        )
        # Should succeed regardless of submitted price (no snapshot = skip check)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Rate-limit tests
# ---------------------------------------------------------------------------

class TestRateLimit:
    def test_rate_limit_blocks_after_ten_orders(self, client, test_db):
        """The 11th order within the window must return 429."""
        user = _create_user(test_db, email="ratelimit@test.com", username="ratelimit")
        _fund_account(test_db, user.id_user, balance_usdt=10_000_000.0)
        token = _make_token(user)

        payload = {"symbol": "BTC", "quantity": 0.0001, "unit_price_usdt": 10_000.0}
        headers = _auth(token)

        for i in range(10):
            resp = client.post("/crypto/trades/buy", json=payload, headers=headers)
            assert resp.status_code == 200, f"order {i+1} unexpectedly failed: {resp.text}"

        resp_11 = client.post("/crypto/trades/buy", json=payload, headers=headers)
        assert resp_11.status_code == 429
        assert "Retry-After" in resp_11.headers

