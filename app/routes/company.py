from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.company import createCompany, readCompany, readCompanies, attachUserToCompany, updateCompany, deleteCompany
from auth.authorization import get_current_user, require_superadmin, CurrentUser

router = APIRouter(
    # prefix="/address",
    tags=["company"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)


# ----------------------------------------------------------------------------------------------------------
# COMPANY TABLE ENDPOINTS
@router.post("/company/save/", status_code=status.HTTP_201_CREATED)
async def create_company(request: base_models.CreateCompanyRequest, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await createCompany(request, db)
      
@router.get("/company/{company_id}", status_code=status.HTTP_200_OK)
async def read_company(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readCompany(company_id, db)

@router.get("/companies/", status_code=status.HTTP_200_OK)
async def list_companies(
    db: db_dependency, 
    current_user: CurrentUser = Depends(require_superadmin())
):
    """List all companies (SuperAdmin only)"""
    return await readCompanies(db)

@router.post("/company/user_to_company/", status_code=status.HTTP_201_CREATED)
async def attach_user_to_company(user_to_company: base_models.CompanyHasUserBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]): 
    return await attachUserToCompany(user_to_company, db) 

@router.put("/company/update/{company_id}", status_code=status.HTTP_200_OK)
async def update_company(company_id: int, company: base_models.CompanyBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updateCompany(company_id, company, db)

@router.delete("/company/delete/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deleteCompany(company_id, db) 

# ----------------------------------------------------------------------------------------------------------