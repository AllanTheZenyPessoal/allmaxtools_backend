from fastapi import APIRouter, Depends, status
from typing import List
from database import base_models
from dependencies import db_dependency
from auth.authorization import (
    get_current_user, 
    require_superadmin, 
    require_admin,
    require_same_company,
    CurrentUser
)
from endpoint.authorization import (
    create_screen,
    create_permission,
    get_screens,
    get_permissions,
    assign_permissions_to_user,
    get_user_permissions,
    create_company,
    create_admin_user
)

router = APIRouter(
    tags=["authorization"],
    responses={404: {"description": "Not found"}}
)

# ----------------------------------------------------------------------------------------------------------
# COMPANY MANAGEMENT (Superadmin only)
@router.post("/companies/", status_code=status.HTTP_201_CREATED)
async def create_company_endpoint(
    company: base_models.CompanyBase,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_superadmin())
):
    """Criar empresa (apenas superadmin)"""
    return await create_company(company, db)

@router.post("/users/admin/", status_code=status.HTTP_201_CREATED)
async def create_admin_user_endpoint(
    user: base_models.UserCreateRequest,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_superadmin())
):
    """Criar usuário admin vinculado a empresa (apenas superadmin)"""
    return await create_admin_user(user, db)

# ----------------------------------------------------------------------------------------------------------
# SCREENS MANAGEMENT (Superadmin only)
@router.post("/screens/", status_code=status.HTTP_201_CREATED)
async def create_screen_endpoint(
    screen: base_models.ScreenBase,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_superadmin())
):
    """Criar nova tela no sistema (apenas superadmin)"""
    return await create_screen(screen, db)

@router.get("/screens/", status_code=status.HTTP_200_OK)
async def get_screens_endpoint(
    db: db_dependency,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Listar todas as telas do sistema"""
    return await get_screens(db)

# ----------------------------------------------------------------------------------------------------------
# PERMISSIONS MANAGEMENT (Superadmin only)
@router.post("/permissions/", status_code=status.HTTP_201_CREATED)
async def create_permission_endpoint(
    permission: base_models.PermissionBase,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_superadmin())
):
    """Criar nova permissão no sistema (apenas superadmin)"""
    return await create_permission(permission, db)

@router.get("/permissions/", status_code=status.HTTP_200_OK)
async def get_permissions_endpoint(
    screen_id: int = None,
    db: db_dependency = Depends(),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Listar todas as permissões do sistema"""
    return await get_permissions(db, screen_id)

# ----------------------------------------------------------------------------------------------------------
# USER PERMISSIONS MANAGEMENT (Admin only)
@router.post("/users/{user_id}/permissions/", status_code=status.HTTP_200_OK)
async def assign_permissions_endpoint(
    user_id: int,
    permissions_data: base_models.UserPermissionAssign,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_admin())
):
    """Atribuir permissões a um usuário (apenas admin da mesma empresa)"""
    from auth.authorization import can_manage_user
    
    if not can_manage_user(user_id, db, current_user):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage users from your own company"
        )
    
    return await assign_permissions_to_user(
        user_id, 
        permissions_data.permission_keys, 
        current_user.id_user,
        db
    )

@router.get("/users/{user_id}/permissions/", status_code=status.HTTP_200_OK)
async def get_user_permissions_endpoint(
    user_id: int,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_admin())
):
    """Obter todas as permissões de um usuário"""
    from auth.authorization import can_manage_user
    
    if not can_manage_user(user_id, db, current_user):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view users from your own company"
        )
    
    return await get_user_permissions(user_id, db)

# ----------------------------------------------------------------------------------------------------------
# CURRENT USER INFO
@router.get("/me/", status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """Obter informações do usuário atual"""
    return {
        "id_user": current_user.id_user,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "company_id": current_user.company_id
    }

@router.get("/me/permissions/", status_code=status.HTTP_200_OK)
async def get_my_permissions(
    current_user: CurrentUser = Depends(get_current_user),
    db: db_dependency = Depends()
):
    """Obter minhas permissões"""
    if current_user.is_superadmin():
        return {"message": "Superadmin has all permissions", "permissions": []}
    
    return await get_user_permissions(current_user.id_user, db)
