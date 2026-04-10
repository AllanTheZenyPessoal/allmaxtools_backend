from fastapi import APIRouter, Depends, status
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models

from endpoint.user import checkLogin, createUser, readUser, readUsers, updateUser, deleteUser

router = APIRouter(
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

 
# ----------------------------------------------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS (Public)
@router.post("/auth/login/", status_code=status.HTTP_200_OK)
async def login(user: base_models.UserLoginRequest, db: db_dependency): 
    return await checkLogin(user, db)  

@router.post("/auth/register/", status_code=status.HTTP_201_CREATED)
async def register(user: base_models.UserRegisterRequest, db: db_dependency): 
    return await createUser(user, db)  

# ----------------------------------------------------------------------------------------------------------
# USER MANAGEMENT ENDPOINTS (Protected)
@router.post("/user/login/", status_code=status.HTTP_200_OK, deprecated=True)
async def check_login(user: base_models.UserBase, db: db_dependency ): 
    return await checkLogin(user, db )  

@router.post("/user/create/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: base_models.UserCreateRequest,
    db: db_dependency, 
    token: Annotated[dict, Depends(verify_token)]
): 
    return await createUser(user, db)  
      
@router.get("/user/read/{user_id}", status_code=status.HTTP_200_OK)
async def read_user(
    user_id: int, 
    db: db_dependency, 
    token: Annotated[dict, Depends(verify_token)]
):
    return await readUser(user_id, db)

@router.get("/user/list/", status_code=status.HTTP_200_OK)
async def read_users(
    db: db_dependency, 
    token: Annotated[dict, Depends(verify_token)]
):
    return await readUsers(db)

@router.put("/user/update/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int, 
    user: base_models.UserBase, 
    db: db_dependency, 
    token: Annotated[dict, Depends(verify_token)]
):
    return await updateUser(user_id, user, db)

@router.delete("/user/delete/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int, 
    db: db_dependency, 
    token: Annotated[dict, Depends(verify_token)]
):
    return await deleteUser(user_id, db)
