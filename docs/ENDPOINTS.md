# AllmaxTools API — Endpoints Reference

Base URL: `https://allmaxtools.com/api`
Auth: `Authorization: Bearer <token>`

---

## Autenticação

### `POST /auth/login/`
Login e geração de token JWT.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "senha123",
  "trade_mode": "live",
  "permanent": false
}
```
- `trade_mode`: `"live"` (padrão) ou `"paper"`
- `permanent`: se `true`, o token não expira

**Response 200:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expired": false,
  "expires_at": "2026-06-09T14:00:00"
}
```
- `expires_at` é `null` quando `permanent: true`

---

## Preços de Criptomoedas

### `GET /crypto/prices/latest`
Retorna o último preço coletado de BTC e ETH.

**Response 200:**
```json
{
  "btc": { "price_usdt": 105000.0, "created_at": "2026-06-09T12:00:00" },
  "eth": { "price_usdt": 2800.0,   "created_at": "2026-06-09T12:00:00" }
}
```

---

### `POST /crypto/prices/history/range`
Histórico de preços de um símbolo por intervalo de datas.

**Body:**
```json
{
  "symbol": "BTC",
  "start_date": "2026-06-02T12:00:00",
  "end_date": "2026-06-09T12:00:00"
}
```

**Response 200:**
```json
{
  "items": [
    { "price_usdt": 104500.0, "created_at": "2026-06-02T12:00:00" }
  ]
}
```

---

## Trades

> Todos os endpoints de trade requerem `Authorization: Bearer <token>`.
> Query param `?mode=live` (padrão) ou `?mode=paper`.
> O `trade_mode` do token deve ser igual ao `mode` do request — caso contrário `403`.

### `POST /crypto/trades/buy`

**Fluxo:**
- `mode=paper` → execução 100% simulada, sem chamar a Binance.
- `mode=live` sem credenciais Binance → execução simulada internamente.
- `mode=live` com credenciais Binance → **ordem MARKET real executada na Binance** antes de atualizar o saldo interno. O preço e a quantidade retornados refletem o fill real.

**Body:**
```json
{
  "symbol": "BTC",
  "unit_price_usdt": 104500.0,
  "quantity": 0.000957,
  "executed_at": "2026-06-09T12:00:00.000Z"
}
```
- `quantity` é **obrigatório** quando há credenciais Binance cadastradas.
- `executed_at` é opcional (default: now).

**Response 200:**
```json
{
  "id_trade": 1,
  "user_id": 1,
  "trade_type": "buy",
  "symbol": "BTC",
  "trade_mode": "live",
  "quantity": 0.000957,
  "unit_price_usdt": 104500.0,
  "total_usdt": 100.03,
  "executed_at": "2026-06-09T12:00:00",
  "created_at": "2026-06-09T12:00:00",
  "balance_usdt": 899.97,
  "holding_quantity": 0.000957,
  "holding_value_usdt": 100.03,
  "avg_cost_usdt": 104500.0,
  "binance_order_id": "123456789"
}
```
- `binance_order_id` é `null` quando não há credenciais Binance.

---

### `POST /crypto/trades/sell`
Mesma estrutura de payload e response que `/trades/buy`, com `trade_type: "sell"`.

---

### `POST /crypto/trades/history`
Histórico de trades do usuário autenticado.

**Body:**
```json
{
  "start_date": "2026-05-10T00:00:00.000Z",
  "end_date": "2026-06-09T00:00:00.000Z",
  "symbol": "BTC",
  "trade_type": "buy"
}
```
- `symbol` e `trade_type` são opcionais.
- `trade_type` aceita `"buy"` ou `"sell"`.

**Response 200:**
```json
{
  "items": [
    {
      "symbol": "BTC",
      "trade_type": "buy",
      "unit_price_usdt": 104500.0,
      "quantity": 0.000957,
      "executed_at": "2026-06-09T12:00:00"
    }
  ]
}
```

---

## Conta

### `GET /account/balance`
`?mode=live|paper`

**Response 200:**
```json
{ "balance_usdt": 500.0 }
```

---

### `GET /account/holdings`
`?mode=live|paper`

**Response 200:**
```json
{
  "user_id": 1,
  "holdings": [
    {
      "symbol": "BTC",
      "trade_mode": "live",
      "quantity": 0.000957,
      "avg_cost_usdt": 104500.0,
      "current_price_usdt": 105000.0,
      "current_value_usdt": 100.49,
      "updated_at": "2026-06-09T12:00:00"
    }
  ]
}
```

---

### `GET /account/portfolio`
`?mode=live|paper`

**Response 200:**
```json
{
  "user_id": 1,
  "trade_mode": "live",
  "balance_usdt": 500.0,
  "total_holdings_value_usdt": 100.49,
  "total_portfolio_value_usdt": 600.49,
  "holdings": [ ... ]
}
```

---

### `POST /account/deposit`
`?mode=live|paper`

**Body:**
```json
{
  "amount_usdt": 100.0,
  "description": "Depósito inicial",
  "user_id": 1
}
```
- `user_id` é opcional. Apenas admins podem depositar para outro usuário.

**Response 200:**
```json
{ "balance_usdt": 600.0 }
```

---

### `POST /account/withdraw`
`?mode=live|paper`

**Body:**
```json
{
  "amount_usdt": 50.0,
  "description": "Saque",
  "user_id": 1
}
```

**Response 200:**
```json
{ "balance_usdt": 550.0 }
```

---

## Binance

> Requer `Authorization: Bearer <token>`.
> A variável de ambiente `BINANCE_ENCRYPTION_KEY` deve estar configurada no servidor.

### `POST /binance/credentials`
Salva ou atualiza as credenciais Binance do usuário. O secret é criptografado em repouso com AES-128 (Fernet) e **nunca** é retornado.

**Body:**
```json
{
  "api_key": "your_binance_api_key",
  "api_secret": "your_binance_api_secret",
  "testnet": false
}
```
- `testnet: true` usa `testnet.binance.vision` em vez de `api.binance.com`.

**Response 200:**
```json
{
  "api_key_hint": "...A3Kz",
  "testnet": false,
  "created_at": "2026-06-09T12:00:00",
  "updated_at": "2026-06-09T12:00:00"
}
```

---

### `GET /binance/credentials`
Retorna informações sobre as credenciais cadastradas (sem expor o secret).

**Response 200:**
```json
{
  "api_key_hint": "...A3Kz",
  "testnet": false,
  "created_at": "2026-06-09T12:00:00",
  "updated_at": "2026-06-09T12:00:00"
}
```

**Response 404:** nenhuma credencial cadastrada.

---

### `DELETE /binance/credentials`
Remove as credenciais da Binance do usuário.

**Response 200:**
```json
{ "message": "Binance credentials removed successfully." }
```

---

### `GET /binance/health`
Verifica a conexão com a Binance, valida a API key e checa permissões de trade.

**Response 200:**
```json
{
  "connected": true,
  "authenticated": true,
  "can_trade": true,
  "testnet": false,
  "account_type": "SPOT",
  "balances": [
    { "asset": "USDT", "free": "1000.00", "locked": "0.00" },
    { "asset": "BTC",  "free": "0.001",   "locked": "0.00" }
  ]
}
```
- `balances` mostra apenas USDT, BTC e ETH com saldo > 0.
- Sempre retorna `200`; use `connected`/`authenticated`/`can_trade` para checar o status.

---

## WebSocket

### `wss://allmaxtools.com/api/crypto/ws/prices`
Recebe atualizações de preço em tempo real.

**Mensagem (servidor → cliente):**
```json
{
  "type": "price_update",
  "data": [
    { "symbol": "BTC", "price_usdt": 104500.0, "created_at": "2026-06-09T12:00:00" },
    { "symbol": "ETH", "price_usdt": 2800.0,   "created_at": "2026-06-09T12:00:00" }
  ]
}
```

---

## Segurança — Checklist Binance

1. **Restrição de IP na Binance**: configure a API key para aceitar apenas o IP do servidor AllmaxTools.
2. **Permissões mínimas**: na Binance, habilite apenas `Spot & Margin Trading` — nunca habilite saques (Withdrawals).
3. **`BINANCE_ENCRYPTION_KEY`**: gere uma chave única por ambiente e guarde-a em segredo:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
4. **Testnet primeiro**: use `"testnet": true` para validar a integração antes de operar com fundos reais.
5. **Rate limit interno**: o sistema bloqueia mais de 10 ordens/minuto por usuário por símbolo (`429 Too Many Requests`).
