from fastapi import APIRouter, Depends, status
from dependencies import db_dependency 
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.branch import createBranch, readBranch, listBranch, updateBranch, deleteBranch 

router = APIRouter(
    # prefix="/address",
    tags=["branch"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)


# ----------------------------------------------------------------------------------------------------------
#  COMPANY BRANCH TABLE ENDPOINTS
@router.get("/branch/read/{branch_id}", status_code=status.HTTP_200_OK)
async def read_branch_by_id(branch_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readBranch(branch_id, db)

@router.get("/branch/list/{company_id}", status_code=status.HTTP_200_OK)
async def read_branch_all(company_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await listBranch(company_id,db)

@router.post("/branch/create/", status_code=status.HTTP_201_CREATED)
async def create_branch(branch: base_models.CompanyBranchBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await createBranch(branch, db)

@router.put("/branch/update/{branch_id}", status_code=status.HTTP_200_OK)
async def update_branch(branch_id: int, branch: base_models.CompanyBranchBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updateBranch(branch_id, branch, db)

@router.delete("/branch/delete/{branch_id}", status_code=status.HTTP_200_OK)
async def delete_branch(branch_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deleteBranch(branch_id, db)
   

# ----------------------------------------------------------------------------------------------------------