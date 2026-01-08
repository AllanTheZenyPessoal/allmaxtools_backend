from fastapi import APIRouter, Depends, Response, status, HTTPException
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated
from database import base_models, db_models  

from endpoint.user import checkLogin, createUser, readUser, readUsers, updateUser, deleteUser
from auth.authorization import (
    get_current_user, 
    require_admin, 
    require_permission,
    require_same_company,
    CurrentUser,
    can_manage_user,
    filter_users_by_company
)

router = APIRouter(
    # prefix="/address",
    tags=["user"],
    # dependencies=[Depends(get_token_header)],
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
    user: base_models.UserBase, 
    db: db_dependency, 
    current_user: CurrentUser = Depends(require_permission("user.create"))
): 
    # Definir role automaticamente baseado no role do usuário logado
    # SuperAdmin cria Admin, Admin cria User
    if current_user.is_superadmin():
        user.role = 'admin'
    elif current_user.role == 'admin':
        user.role = 'user'
        # Admin só pode criar usuários da própria empresa
        user.company_id = current_user.company_id
    else:
        # User não pode criar usuários
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users with 'user' role cannot create new users"
        )
    
    # Validar company_id para admin (deve ter empresa)
    if current_user.role == 'admin' and not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin must belong to a company to create users"
        )
    
    return await createUser(user, db)  
      
@router.get("/user/read/{user_id}", status_code=status.HTTP_200_OK)
async def read_user(
    user_id: int, 
    db: db_dependency, 
    current_user: CurrentUser = Depends(require_permission("user.read"))
):
    # Verificar se pode gerenciar este usuário
    if not can_manage_user(user_id, db, current_user):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view users from your own company"
        )
    
    user_data = await readUser(user_id, db)
    
    # Se não é um HTTPException, adicionar informações de role e permissões
    if hasattr(user_data, 'role'):
        from endpoint.authorization import get_user_permissions
        permissions = await get_user_permissions(user_id, db)
        return {
            **user_data.__dict__,
            "role": user_data.role,
            "company_id": user_data.company_id,
            "permissions": permissions if not current_user.is_superadmin() else "All permissions (superadmin)"
        }
    
    return user_data

@router.get("/user/list/", status_code=status.HTTP_200_OK)
async def read_users(
    db: db_dependency, 
    current_user: CurrentUser = Depends(require_permission("user.list"))
):
    # Filtrar usuários por empresa (exceto superadmin)
    from database import db_models
    
    query = db.query(db_models.User)
    
    # Filtrar por role baseado no tipo de usuário logado
    if current_user.is_superadmin():
        # SuperAdmin vê apenas usuários com role 'superadmin' e 'admin'
        query = query.filter(db_models.User.role.in_(['superadmin', 'admin']))
        query = query.filter(db_models.User.id_user != current_user.id_user)
    elif current_user.role == 'admin':
        # Admin vê apenas usuários com role 'user' da mesma empresa
        query = query.filter(db_models.User.role == 'user')
        query = query.filter(db_models.User.company_id == current_user.company_id)
        query = query.filter(db_models.User.id_user != current_user.id_user)
    else:
        # Outros roles não veem nenhum usuário
        return []
    
    users = query.all()
    
    # Adicionar informações de role para cada usuário
    users_with_roles = []
    for user in users:
        user_dict = user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)  # Remove SQLAlchemy metadata
        users_with_roles.append(user_dict)
    
    return users_with_roles

@router.put("/user/update/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int, 
    user: base_models.UserBase, 
    db: db_dependency, 
    current_user: CurrentUser = Depends(require_permission("user.update"))
):
    # Verificar se pode gerenciar este usuário
    if not can_manage_user(user_id, db, current_user):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update users from your own company"
        )
    
    return await updateUser(user_id, user, db)

@router.delete("/user/delete/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int, 
    db: db_dependency, 
    current_user: CurrentUser = Depends(require_permission("user.delete"))
):
    # Verificar se pode gerenciar este usuário
    if not can_manage_user(user_id, db, current_user):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete users from your own company"
        )
    
    return await deleteUser(user_id, db)

# ----------------------------------------------------------------------------------------------------------
# USER PERMISSIONS ENDPOINTS (Protected)
@router.get("/user/{user_id}/permissions", status_code=status.HTTP_200_OK)
async def get_user_permissions(
    user_id: int,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_permission("user.read"))
):
    """
    Retorna todas as permissões de um usuário específico
    """
    # Verificar se pode gerenciar este usuário
    if not can_manage_user(user_id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view permissions of users from your own company"
        )
    
    try:
        # Buscar usuário
        user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if not user:
    
            raise HTTPException(status_code=404, detail="User not found")
        
        # Se for superadmin, tem todas as permissões
        if user.role == 'superadmin':
            return {
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "company_id": user.company_id,
                "permissions": "ALL_PERMISSIONS",
                "note": "Superadmin has access to all system functions"
            }
        
        # Buscar permissões específicas do usuário
        permissions_query = db.query(
            db_models.Permission.name,
            db_models.Permission.description
        ).join(
            db_models.UserPermission,
            db_models.Permission.id_permission == db_models.UserPermission.permission_id
        ).filter(
            db_models.UserPermission.user_id == user_id
        ).all()
        
        permissions_list = [
            {
                "permission": perm.name,
                "description": perm.description
            }
            for perm in permissions_query
        ]
        
        return {
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "company_id": user.company_id,
            "permissions": permissions_list,
            "total_permissions": len(permissions_list)
        }
        
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user permissions: {str(e)}"
        )

@router.get("/permissions", status_code=status.HTTP_200_OK)
async def list_all_permissions(
    db: db_dependency,
    current_user: CurrentUser = Depends(require_permission("user.read"))
):
    """
    Lista todas as permissões disponíveis no sistema
    """
    try:
        permissions = db.query(db_models.Permission).all()
        
        permissions_list = [
            {
                "id": perm.id_permission,
                "name": perm.name,
                "description": perm.description
            }
            for perm in permissions
        ]
        
        return {
            "permissions": permissions_list,
            "total": len(permissions_list)
        }
        
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving permissions: {str(e)}"
        )

@router.post("/user/{user_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_user(
    user_id: int,
    permission_data: dict,
    db: db_dependency,
    current_user: CurrentUser = Depends(require_permission("user.create"))
):
    """
    Atribui uma permissão específica a um usuário
    Body: {"permission_id": 1}
    """
    # Verificar se pode gerenciar este usuário
    if not can_manage_user(user_id, db, current_user):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage permissions of users from your own company"
        )
    
    try:
        permission_id = permission_data.get("permission_id")
        if not permission_id:
    
            raise HTTPException(status_code=400, detail="permission_id is required")
        
        # Verificar se usuário existe
        user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if not user:
    
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verificar se permissão existe
        permission = db.query(db_models.Permission).filter(
            db_models.Permission.id_permission == permission_id
        ).first()
        if not permission:
    
            raise HTTPException(status_code=404, detail="Permission not found")
        
        # Verificar se já existe a associação
        existing = db.query(db_models.UserPermission).filter(
            db_models.UserPermission.user_id == user_id,
            db_models.UserPermission.permission_id == permission_id
        ).first()
        
        if existing:
    
            raise HTTPException(status_code=400, detail="Permission already assigned to user")
        
        # Criar nova associação
        new_user_permission = db_models.UserPermission(
            user_id=user_id,
            permission_id=permission_id
        )
        
        db.add(new_user_permission)
        db.commit()
        
        return {
            "message": "Permission assigned successfully",
            "user_id": user_id,
            "permission_id": permission_id,
            "permission_name": permission.name
        }
        
    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning permission: {str(e)}"
        )

# ----------------------------------------------------------------------------------------------------------