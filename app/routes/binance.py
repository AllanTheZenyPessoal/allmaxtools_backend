"""
Binance credential management and health-check endpoints.

Security model:
- API key and secret are encrypted at rest with Fernet (AES-128-CBC).
- The secret is NEVER returned in any response.
- Only the last 4 chars of the API key are exposed as a hint.
- Encryption key must be set via BINANCE_ENCRYPTION_KEY env var.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import base_models, db_models
from dependencies import get_db
from services.binance_client import BinanceClient
from services.encryption import decrypt, encrypt
from token_utils.apikey_generator import verify_token

router = APIRouter(tags=["binance"], prefix="/binance")

_RELEVANT_ASSETS = {"USDT", "BTC", "ETH"}


def _get_creds(db: Session, user_id: int) -> db_models.BinanceCredentials:
    creds = (
        db.query(db_models.BinanceCredentials)
        .filter(db_models.BinanceCredentials.user_id == user_id)
        .first()
    )
    if creds is None:
        raise HTTPException(status_code=404, detail="No Binance credentials found for this user.")
    return creds


def _build_client(creds: db_models.BinanceCredentials) -> BinanceClient:
    return BinanceClient(
        api_key=decrypt(creds.api_key_encrypted),
        api_secret=decrypt(creds.api_secret_encrypted),
        testnet=bool(creds.testnet),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/credentials",
    response_model=base_models.BinanceCredentialsResponse,
    summary="Salvar / atualizar credenciais Binance",
    description=(
        "Salva ou atualiza a API key e o secret da Binance do usuário autenticado. "
        "Os valores são criptografados em repouso com AES-128 (Fernet). "
        "O secret **nunca** é retornado em nenhuma resposta."
    ),
)
async def save_credentials(
    payload: base_models.BinanceCredentialsRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
) -> base_models.BinanceCredentialsResponse:
    user_id: int = token["id_user"]

    api_key_hint = "..." + payload.api_key[-4:]
    api_key_enc = encrypt(payload.api_key)
    api_secret_enc = encrypt(payload.api_secret)

    creds = (
        db.query(db_models.BinanceCredentials)
        .filter(db_models.BinanceCredentials.user_id == user_id)
        .first()
    )

    if creds is None:
        creds = db_models.BinanceCredentials(
            user_id=user_id,
            api_key_encrypted=api_key_enc,
            api_secret_encrypted=api_secret_enc,
            api_key_hint=api_key_hint,
            testnet=payload.testnet,
        )
        db.add(creds)
    else:
        creds.api_key_encrypted = api_key_enc
        creds.api_secret_encrypted = api_secret_enc
        creds.api_key_hint = api_key_hint
        creds.testnet = payload.testnet

    db.commit()
    db.refresh(creds)

    return base_models.BinanceCredentialsResponse(
        api_key_hint=str(creds.api_key_hint),
        testnet=bool(creds.testnet),
        created_at=creds.created_at,
        updated_at=creds.updated_at,
    )


@router.get(
    "/credentials",
    response_model=base_models.BinanceCredentialsResponse,
    summary="Verificar credenciais Binance cadastradas",
    description="Retorna informações sobre as credenciais cadastradas (sem expor o secret).",
)
async def get_credentials(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
) -> base_models.BinanceCredentialsResponse:
    creds = _get_creds(db, token["id_user"])
    return base_models.BinanceCredentialsResponse(
        api_key_hint=str(creds.api_key_hint),
        testnet=bool(creds.testnet),
        created_at=creds.created_at,
        updated_at=creds.updated_at,
    )


@router.delete(
    "/credentials",
    summary="Remover credenciais Binance",
    description="Remove as credenciais Binance do usuário autenticado.",
)
async def delete_credentials(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
) -> dict:
    creds = _get_creds(db, token["id_user"])
    db.delete(creds)
    db.commit()
    return {"message": "Binance credentials removed successfully."}


@router.get(
    "/health",
    response_model=base_models.BinanceHealthResponse,
    summary="Verificar saúde da conta Binance",
    description=(
        "Testa a conexão com a Binance, valida a API key e verifica se a conta "
        "tem permissão para negociar (SPOT). Retorna os saldos relevantes (USDT, BTC, ETH)."
    ),
)
async def binance_health(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
) -> base_models.BinanceHealthResponse:
    creds = _get_creds(db, token["id_user"])
    client = _build_client(creds)

    connected = False
    authenticated = False
    can_trade = False
    account_type = None
    balances: list = []

    try:
        connected = await client.ping()
    except Exception:
        return base_models.BinanceHealthResponse(
            connected=False,
            authenticated=False,
            can_trade=False,
            testnet=bool(creds.testnet),
        )

    try:
        account = await client.get_account()
        authenticated = True
        can_trade = account.get("canTrade", False)
        account_type = account.get("accountType")
        balances = [
            {"asset": b["asset"], "free": b["free"], "locked": b["locked"]}
            for b in account.get("balances", [])
            if b["asset"] in _RELEVANT_ASSETS and (float(b["free"]) > 0 or float(b["locked"]) > 0)
        ]
    except HTTPException:
        pass

    return base_models.BinanceHealthResponse(
        connected=connected,
        authenticated=authenticated,
        can_trade=can_trade,
        testnet=bool(creds.testnet),
        account_type=account_type,
        balances=balances,
    )
