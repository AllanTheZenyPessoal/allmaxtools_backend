"""
Testes para os endpoints de credenciais Binance e integração de trade real.

Estratégia de mock:
- Fernet encryption: mockada via BINANCE_ENCRYPTION_KEY env var com chave gerada.
- BinanceClient.ping / get_account / market_order: mockados com unittest.mock.patch.
- Nenhuma chamada real à Binance é feita nestes testes.
"""
import os
import pytest
from cryptography.fernet import Fernet
from unittest.mock import AsyncMock, patch

from database import db_models  # type: ignore
from endpoint.user import get_password_hash  # type: ignore
from token_utils.apikey_generator import create_access_token  # type: ignore

# Gera chave Fernet válida para os testes
_TEST_FERNET_KEY = Fernet.generate_key().decode()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, *, email="binance@test.com", username="binanceuser"):
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


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _fund_account(db, user_id, balance_usdt=10_000.0):
    account = db_models.UserAccount(user_id=user_id, balance_usdt=balance_usdt)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


# ---------------------------------------------------------------------------
# Fixtures de mock para encryption
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    monkeypatch.setenv("BINANCE_ENCRYPTION_KEY", _TEST_FERNET_KEY)


# ---------------------------------------------------------------------------
# Testes de credenciais
# ---------------------------------------------------------------------------

class TestBinanceCredentials:
    def test_save_credentials_creates_entry(self, client, test_db):
        user = _create_user(test_db)
        token = _make_token(user)

        resp = client.post(
            "/binance/credentials",
            json={"api_key": "TESTKEY1234567890", "api_secret": "TESTSECRET1234567890", "testnet": False},
            headers=_auth(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["api_key_hint"] == "...7890"
        assert data["testnet"] is False
        assert "api_secret" not in data
        assert "api_key" not in data

    def test_save_credentials_updates_existing(self, client, test_db):
        user = _create_user(test_db, email="update@test.com", username="updateuser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "OLDKEY1234567890", "api_secret": "OLDSECRET", "testnet": False},
            headers=_auth(token),
        )
        resp = client.post(
            "/binance/credentials",
            json={"api_key": "NEWKEY1234ABCD", "api_secret": "NEWSECRET1234", "testnet": True},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_key_hint"] == "...ABCD"
        assert data["testnet"] is True

        # Only one row in DB
        rows = test_db.query(db_models.BinanceCredentials).filter_by(user_id=user.id_user).all()
        assert len(rows) == 1

    def test_get_credentials_returns_hint(self, client, test_db):
        user = _create_user(test_db, email="get@test.com", username="getuser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "MYAPIKEY12345678", "api_secret": "MYSECRET123", "testnet": False},
            headers=_auth(token),
        )
        resp = client.get("/binance/credentials", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["api_key_hint"] == "...5678"

    def test_get_credentials_404_when_none(self, client, test_db):
        user = _create_user(test_db, email="none@test.com", username="noneuser")
        token = _make_token(user)

        resp = client.get("/binance/credentials", headers=_auth(token))
        assert resp.status_code == 404

    def test_delete_credentials(self, client, test_db):
        user = _create_user(test_db, email="del@test.com", username="deluser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "DELKEY1234567890", "api_secret": "DELSECRET123456", "testnet": False},
            headers=_auth(token),
        )
        resp = client.delete("/binance/credentials", headers=_auth(token))
        assert resp.status_code == 200
        assert "removed" in resp.json()["message"].lower()

        # Confirm it's gone
        resp2 = client.get("/binance/credentials", headers=_auth(token))
        assert resp2.status_code == 404

    def test_credentials_require_auth(self, client, test_db):
        resp = client.post(
            "/binance/credentials",
            json={"api_key": "K" * 20, "api_secret": "S" * 20, "testnet": False},
        )
        assert resp.status_code in (401, 403)

    def test_secret_never_returned(self, client, test_db):
        user = _create_user(test_db, email="secret@test.com", username="secretuser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "KEYABCDEF1234567", "api_secret": "MYSUPERSECRET123", "testnet": False},
            headers=_auth(token),
        )
        resp = client.get("/binance/credentials", headers=_auth(token))
        response_text = resp.text
        assert "MYSUPERSECRET123" not in response_text
        assert "api_secret" not in response_text


# ---------------------------------------------------------------------------
# Testes de health check (Binance mockada)
# ---------------------------------------------------------------------------

class TestBinanceHealth:
    def test_health_connected_and_can_trade(self, client, test_db):
        user = _create_user(test_db, email="health@test.com", username="healthuser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "HEALTHKEY1234567", "api_secret": "HEALTHSECRET1234", "testnet": False},
            headers=_auth(token),
        )

        mock_account = {
            "canTrade": True,
            "accountType": "SPOT",
            "balances": [
                {"asset": "USDT", "free": "1000.00", "locked": "0.00"},
                {"asset": "BTC", "free": "0.001", "locked": "0.00"},
                {"asset": "XRP", "free": "0.00", "locked": "0.00"},  # should be filtered
            ],
        }

        with patch("services.binance_client.BinanceClient.ping", new_callable=AsyncMock, return_value=True), \
             patch("services.binance_client.BinanceClient.get_account", new_callable=AsyncMock, return_value=mock_account):
            resp = client.get("/binance/health", headers=_auth(token))

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["connected"] is True
        assert data["authenticated"] is True
        assert data["can_trade"] is True
        assert data["account_type"] == "SPOT"
        assets = [b["asset"] for b in data["balances"]]
        assert "USDT" in assets
        assert "BTC" in assets
        assert "XRP" not in assets  # zero balance filtered

    def test_health_unreachable_binance(self, client, test_db):
        user = _create_user(test_db, email="unreach@test.com", username="unreachuser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "UNREACHKEY123456", "api_secret": "UNREACHSECRET123", "testnet": False},
            headers=_auth(token),
        )

        with patch("services.binance_client.BinanceClient.ping", new_callable=AsyncMock, side_effect=Exception("timeout")):
            resp = client.get("/binance/health", headers=_auth(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False
        assert data["authenticated"] is False
        assert data["can_trade"] is False

    def test_health_invalid_api_key(self, client, test_db):
        from fastapi import HTTPException as FastHTTPException
        user = _create_user(test_db, email="invalid@test.com", username="invaliduser")
        token = _make_token(user)

        client.post(
            "/binance/credentials",
            json={"api_key": "INVALIDKEY123456", "api_secret": "INVALIDSECRET123", "testnet": False},
            headers=_auth(token),
        )

        with patch("services.binance_client.BinanceClient.ping", new_callable=AsyncMock, return_value=True), \
             patch("services.binance_client.BinanceClient.get_account", new_callable=AsyncMock,
                   side_effect=FastHTTPException(status_code=502, detail="Invalid API key")):
            resp = client.get("/binance/health", headers=_auth(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["authenticated"] is False


# ---------------------------------------------------------------------------
# Testes de trade live com Binance mockada
# ---------------------------------------------------------------------------

class TestLiveTradeBinance:
    def _setup(self, test_db, email, username):
        user = _create_user(test_db, email=email, username=username)
        _fund_account(test_db, user.id_user, balance_usdt=50_000.0)
        token = _make_token(user)
        return user, token

    def _save_creds(self, client, token):
        client.post(
            "/binance/credentials",
            json={"api_key": "TRADEKEY12345678", "api_secret": "TRADESECRET12345", "testnet": True},
            headers=_auth(token),
        )

    def test_live_buy_with_credentials_calls_binance(self, client, test_db):
        user, token = self._setup(test_db, "buylive@test.com", "buylive")
        self._save_creds(client, token)

        mock_fill = {
            "order_id": "111222333",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "executed_qty": 0.1,
            "avg_price": 50_100.0,
            "total_usdt": 5_010.0,
            "fees_usdt": 5.01,
            "status": "FILLED",
        }

        with patch("services.binance_client.BinanceClient.market_order",
                   new_callable=AsyncMock, return_value=mock_fill):
            resp = client.post(
                "/crypto/trades/buy",
                json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
                headers=_auth(token),
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["binance_order_id"] == "111222333"
        # Price must come from Binance fill, not the submitted price
        assert data["unit_price_usdt"] == pytest.approx(50_100.0, abs=0.01)
        assert data["quantity"] == pytest.approx(0.1, abs=1e-8)

    def test_live_sell_with_credentials_calls_binance(self, client, test_db):
        user, token = self._setup(test_db, "selllive@test.com", "selllive")

        # Give user a holding to sell
        holding = db_models.UserHolding(
            user_id=user.id_user, symbol="BTC", quantity=0.5,
            avg_cost_usdt=50_000.0, current_value_usdt=25_000.0,
        )
        test_db.add(holding)
        test_db.commit()

        self._save_creds(client, token)

        mock_fill = {
            "order_id": "444555666",
            "symbol": "BTCUSDT",
            "side": "SELL",
            "executed_qty": 0.2,
            "avg_price": 51_000.0,
            "total_usdt": 10_200.0,
            "fees_usdt": 10.20,
            "status": "FILLED",
        }

        with patch("services.binance_client.BinanceClient.market_order",
                   new_callable=AsyncMock, return_value=mock_fill):
            resp = client.post(
                "/crypto/trades/sell",
                json={"symbol": "BTC", "quantity": 0.2, "unit_price_usdt": 50_000.0},
                headers=_auth(token),
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["binance_order_id"] == "444555666"
        assert data["unit_price_usdt"] == pytest.approx(51_000.0, abs=0.01)

    def test_live_buy_without_credentials_uses_simulated_flow(self, client, test_db):
        """Sem credenciais Binance, o fluxo simulado interno deve ser usado."""
        user, token = self._setup(test_db, "nosim@test.com", "nosimuser")

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["binance_order_id"] is None

    def test_live_buy_requires_quantity_when_credentials_present(self, client, test_db):
        """quantity obrigatória quando há credenciais Binance."""
        user, token = self._setup(test_db, "noquantity@test.com", "noquantityuser")
        self._save_creds(client, token)

        resp = client.post(
            "/crypto/trades/buy",
            json={"symbol": "BTC", "unit_price_usdt": 50_000.0},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "quantity" in resp.json()["detail"].lower()

    def test_live_buy_binance_error_returns_502(self, client, test_db):
        """Se a Binance retornar erro, o trade não é registrado internamente."""
        from fastapi import HTTPException as FastHTTPException
        user, token = self._setup(test_db, "binerr@test.com", "binerr")
        self._save_creds(client, token)

        with patch("services.binance_client.BinanceClient.market_order",
                   new_callable=AsyncMock,
                   side_effect=FastHTTPException(status_code=502, detail="Binance order failed")):
            resp = client.post(
                "/crypto/trades/buy",
                json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
                headers=_auth(token),
            )

        assert resp.status_code == 502

        # Internal state must NOT be modified
        account = test_db.query(db_models.UserAccount).filter_by(user_id=user.id_user).first()
        assert account.balance_usdt == pytest.approx(50_000.0, abs=0.01)

    def test_paper_mode_never_calls_binance(self, client, test_db):
        """Paper trade não chama Binance mesmo que haja credenciais."""
        from token_utils.apikey_generator import create_access_token  # type: ignore

        user = _create_user(test_db, email="papernobinance@test.com", username="papernobinance")
        paper_balance = db_models.PaperBalance(user_id=user.id_user, balance_usdt=100_000.0)
        test_db.add(paper_balance)
        test_db.commit()

        paper_token, _ = create_access_token(
            email=user.email, username=user.username,
            id_user=user.id_user, role=user.role,
            company_id=user.company_id, trade_mode="paper",
        )

        # Save credentials (should be ignored for paper mode)
        live_token = _make_token(user)
        client.post(
            "/binance/credentials",
            json={"api_key": "PAPERKEY12345678", "api_secret": "PAPERSECRET12345", "testnet": False},
            headers=_auth(live_token),
        )

        with patch("services.binance_client.BinanceClient.market_order",
                   new_callable=AsyncMock) as mock_order:
            resp = client.post(
                "/crypto/trades/buy?mode=paper",
                json={"symbol": "BTC", "quantity": 0.1, "unit_price_usdt": 50_000.0},
                headers=_auth(paper_token),
            )

        assert resp.status_code == 200, resp.text
        mock_order.assert_not_called()
        assert resp.json()["binance_order_id"] is None
