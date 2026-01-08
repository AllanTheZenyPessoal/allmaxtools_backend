from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.paymentmethod import createPaymentMethod, readPaymentMethodById, updatePaymentMethod, deletePaymentMethod, listPaymentMethod

router = APIRouter(
    # prefix="/address",
    tags=["paymentmethod"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)


# ----------------------------------------------------------------------------------------------------------
# COMPANY PAYMENT METHOD TABLE ENDPOINTS
@router.get("/paymentmethod/read/{paymentmethod_id}", status_code=status.HTTP_200_OK)
async def read_paymentmethod(paymentmethod_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readPaymentMethodById(paymentmethod_id, db) 

@router.get("/paymentmethod/list/{company_id}", status_code=status.HTTP_200_OK)
async def list_paymentmethod(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await listPaymentMethod(company_id, db)

@router.post("/paymentmethod/create/", status_code=status.HTTP_201_CREATED)
async def create_paymentmethod(paymentmethod: base_models.CompanyPaymentMethodBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await createPaymentMethod(paymentmethod, db)

@router.put("/paymentmethod/update/{paymentmethod_id}", status_code=status.HTTP_200_OK)
async def update_paymentmethod(paymentmethod_id: int, paymentmethod: base_models.CompanyPaymentMethodBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updatePaymentMethod(paymentmethod_id, paymentmethod, db)

@router.delete("/paymentmethod/delete/{paymentmethod_id}", status_code=status.HTTP_200_OK)
async def delete_paymentmethod(paymentmethod_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deletePaymentMethod(paymentmethod_id, db)
# ----------------------------------------------------------------------------------------------------------