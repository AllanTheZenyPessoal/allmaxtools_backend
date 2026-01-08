from fastapi import APIRouter, Depends, status
from dependencies import db_dependency 
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models

from endpoint.address import createAddress, readAddress, updateAddress, deleteAddress

router = APIRouter(
    # prefix="/address",
    tags=["address"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)

  
# ----------------------------------------------------------------------------------------------------------
#  ADDRESS TABLE ENDPOINTS
@router.get("/address/read/{address_id}", status_code=status.HTTP_200_OK)
async def read_address( address_id: int, db: db_dependency ):
    return await readAddress(address_id, db) 

@router.post("/address/create/", status_code=status.HTTP_201_CREATED)
async def create_address( address: base_models.AddressBase, db: db_dependency, token: Annotated[str, Depends(verify_token)]):
    return await createAddress(address, db) 

@router.put("/address/update/{address_id}", status_code=status.HTTP_200_OK)
async def update_address( address_id: int, address: base_models.AddressBase, db: db_dependency, token: Annotated[str, Depends(verify_token)] ):
    return await updateAddress(address_id, address, db)

@router.delete("/address/delete/{address_id}", status_code=status.HTTP_200_OK)
async def delete_address( address_id: int, db: db_dependency, token: Annotated[str, Depends(verify_token)] ):
    return await deleteAddress(address_id, db) 

# ----------------------------------------------------------------------------------------------------------