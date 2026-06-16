import traceback
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import base_models
from dependencies import get_db
from endpoint.crypto import crypto_collector_service
from token_utils.apikey_generator import verify_token

router = APIRouter(tags=["account"], prefix="/account")


def _assert_mode_matches_token(token: dict, mode: str) -> None:
    """Raise 403 when the token's trade_mode claim disagrees with the request mode."""
    token_mode = token.get("trade_mode", "live")
    if token_mode != mode:
        raise HTTPException(
            status_code=403,
            detail=f"token is bound to '{token_mode}' mode; request uses '{mode}' mode",
        )


@router.get(
    "/balance",
    response_model=base_models.UserAccountResponse,
    summary="Saldo da conta",
    description="Retorna o saldo em USDT disponível na conta do usuário autenticado.",
)
async def get_balance(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)
    return crypto_collector_service.get_account_balance(db, token["id_user"], mode)


@router.get(
    "/holdings",
    response_model=base_models.UserHoldingsResponse,
    summary="Holdings do usuário",
    description="Retorna as posições abertas (criptomoedas em carteira) do usuário autenticado.",
)
async def get_holdings(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)
    return crypto_collector_service.get_holdings(db, token["id_user"], mode)


@router.get(
    "/portfolio",
    response_model=base_models.PortfolioResponse,
    summary="Portfólio completo",
    description="Retorna saldo, holdings e valor total consolidado do portfólio do usuário.",
)
async def get_portfolio(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)
    return crypto_collector_service.get_portfolio(db, token["id_user"], mode)


@router.post(
    "/deposit",
    response_model=base_models.UserAccountResponse,
    summary="Depositar saldo",
    description="Credita um valor em USDT na conta do usuário. `user_id` é opcional — apenas admins podem depositar para outro usuário.",
)
async def deposit_balance(
    payload: base_models.AccountMutationRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)
    try:
        return crypto_collector_service.deposit_balance(db, token, payload, mode)
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/withdraw",
    response_model=base_models.UserAccountResponse,
    summary="Sacar saldo",
    description="Debita um valor em USDT da conta do usuário. Retorna erro 400 se o saldo for insuficiente.",
)
async def withdraw_balance(
    payload: base_models.AccountMutationRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)
    try:
        return crypto_collector_service.withdraw_balance(db, token, payload, mode)
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))