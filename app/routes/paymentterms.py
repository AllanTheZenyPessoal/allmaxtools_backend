from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.paymentterms import createPaymentTerm, readPaymentTermById, listPaymentTerm, updatePaymentTerm, deletePaymentTerm

router = APIRouter(
    # prefix="/address",
    tags=["paymentterm"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)



# ----------------------------------------------------------------------------------------------------------
# COMPANY PAYMENT TERM TABLE ENDPOINTS
@router.get("/paymentterm/read/{payment_term_id}", status_code=status.HTTP_200_OK)
async def read_paymentterm(payment_term_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readPaymentTermById(payment_term_id, db)

@router.get("/paymentterm/list/{company_id}", status_code=status.HTTP_200_OK)
async def list_paymentterm(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await listPaymentTerm(company_id, db)

@router.post("/paymentterm/create/", status_code=status.HTTP_201_CREATED)
async def create_paymentterm(paymentterm: base_models.CompanyPaymentTermBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await createPaymentTerm(paymentterm, db)

@router.put("/paymentterm/update/{payment_term_id}", status_code=status.HTTP_200_OK)
async def update_paymentterm(payment_term_id: int, paymentterm: base_models.CompanyPaymentTermBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updatePaymentTerm(payment_term_id, paymentterm, db)

@router.delete("/paymentterm/delete/{payment_term_id}", status_code=status.HTTP_200_OK)
async def delete_paymentterm(payment_term_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deletePaymentTerm(payment_term_id, db)
# ----------------------------------------------------------------------------------------------------------