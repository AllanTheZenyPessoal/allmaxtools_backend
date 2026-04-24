from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import base_models
from dependencies import get_db
from endpoint.crypto import crypto_collector_service
from token_utils.apikey_generator import verify_token

router = APIRouter(tags=["account"], prefix="/account")


@router.get("/balance", response_model=base_models.UserAccountResponse)
async def get_balance(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.get_account_balance(db, token["id_user"])


@router.get("/holdings", response_model=base_models.UserHoldingsResponse)
async def get_holdings(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.get_holdings(db, token["id_user"])


@router.get("/portfolio", response_model=base_models.PortfolioResponse)
async def get_portfolio(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.get_portfolio(db, token["id_user"])


@router.post("/deposit", response_model=base_models.UserAccountResponse)
async def deposit_balance(
    payload: base_models.AccountMutationRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.deposit_balance(db, token, payload)


@router.post("/withdraw", response_model=base_models.UserAccountResponse)
async def withdraw_balance(
    payload: base_models.AccountMutationRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.withdraw_balance(db, token, payload)