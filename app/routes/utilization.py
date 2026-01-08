from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.utilization import createUtilization, readUtilizationById, updateUtilization, deleteUtilization, listUtilization

router = APIRouter(
    # prefix="/address",
    tags=["utilization"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)


# ----------------------------------------------------------------------------------------------------------
# COMPANY UTILIZATION TABLE ENDPOINTS
@router.get("/utilization/read/{utilization_id}", status_code=status.HTTP_200_OK)
async def read_utilization(utilization_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readUtilizationById(utilization_id, db)

@router.get("/utilization/list/{company_id}", status_code=status.HTTP_200_OK)
async def list_utilization(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await listUtilization(company_id, db)

@router.post("/utilization/create/", status_code=status.HTTP_201_CREATED)
async def create_utilization(utilization: base_models.CompanyUtilizationBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await createUtilization(utilization, db)

@router.put("/utilization/update/{utilization_id}", status_code=status.HTTP_200_OK)
async def update_utilization(utilization_id: int, utilization: base_models.CompanyUtilizationBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updateUtilization(utilization_id, utilization, db)

@router.delete("/utilization/delete/{utilization_id}", status_code=status.HTTP_200_OK)
async def delete_utilization(utilization_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deleteUtilization(utilization_id, db)
# ----------------------------------------------------------------------------------------------------------