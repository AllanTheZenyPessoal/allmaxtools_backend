from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models  

from endpoint.businnesspartner import createBusinnespartner, readBusinnespartner, updateBusinnespartner, deleteBusinnespartner, listBusinnespartners

router = APIRouter(
    # prefix="/address",
    tags=["businnespartner"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)



# ----------------------------------------------------------------------------------------------------------
#  BUSINESS PARTNER TABLE ENDPOINTS
@router.get("/businnespartner/read/{businnespartner_id}", status_code=status.HTTP_200_OK)
async def read_businnespartner(businnespartner_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await readBusinnespartner(businnespartner_id, db)

@router.post("/businnespartner/create/", status_code=status.HTTP_201_CREATED)
async def create_businnespartner(businnespartner: base_models.BusinessPartnerBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):   
    return await createBusinnespartner(businnespartner, db)
      
@router.put("/businnespartner/update/{businnespartner_id}", status_code=status.HTTP_200_OK)
async def update_businnespartner(businnespartner_id: int, businnespartner: base_models.BusinessPartnerBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await updateBusinnespartner(businnespartner_id, businnespartner, db)

@router.delete("/businnespartner/delete/{businnespartner_id}", status_code=status.HTTP_200_OK)
async def delete_businnespartner(businnespartner_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await deleteBusinnespartner(businnespartner_id, db)

@router.get("/businnespartner/list/{data}", status_code=status.HTTP_200_OK)
async def list_businnespartners(data: str, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await listBusinnespartners(data, db) 

# ----------------------------------------------------------------------------------------------------------