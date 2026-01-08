from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.freight import createFreight, readFreight, updateFreight, deleteFreight, listFreight

router = APIRouter(
    # prefix="/address",
    tags=["freight"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)


# ----------------------------------------------------------------------------------------------------------
# COMPANY FREIGHT TABLE ENDPOINTS
@router.get("/freight/list/{company_id}", status_code=status.HTTP_200_OK)
async def list_company_freight_all(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await listFreight(company_id, db)
 
@router.get("/freight/read/{freight_id}", status_code=status.HTTP_200_OK)
async def read_company_freight(freight_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readFreight(freight_id, db)

@router.post("/freight/create/", status_code=status.HTTP_201_CREATED)
async def create_company_freight(company: base_models.CompanyFreightBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):   
    return await createFreight(company, db)

@router.put("/freight/update/{freight_id}", status_code=status.HTTP_200_OK)
async def update_company_freight(freight_id: int, freight: base_models.CompanyFreightBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updateFreight(freight_id, freight, db)
 
@router.delete("/freight/delete/{freight_id}", status_code=status.HTTP_200_OK)
async def delete_company_freight(freight_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deleteFreight(freight_id, db)

# ----------------------------------------------------------------------------------------------------------