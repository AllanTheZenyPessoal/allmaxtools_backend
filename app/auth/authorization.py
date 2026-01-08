from typing import Optional, List, Callable
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from functools import wraps
from sqlalchemy.orm import Session
from database import db_models
from dependencies import db_dependency, get_db
from token_utils.apikey_generator import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "user": 1,
    "admin": 2,
    "superadmin": 3
}

class CurrentUser:
    """Classe para representar o usuário atual autenticado"""
    def __init__(self, id_user: int, email: str, username: str, role: str, company_id: Optional[int] = None):
        self.id_user = id_user
        self.email = email
        self.username = username
        self.role = role
        self.company_id = company_id
    
    def has_role(self, min_role: str) -> bool:
        """Verifica se o usuário tem pelo menos o role especificado"""
        user_level = ROLE_HIERARCHY.get(self.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)
        return user_level >= required_level
    
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"
    
    def is_admin(self) -> bool:
        return self.role in ["admin", "superadmin"]
    
    def is_same_company(self, company_id: int) -> bool:
        """Verifica se o usuário pertence à mesma empresa"""
        if self.is_superadmin():
            return True  # Superadmin pode acessar qualquer empresa
        return self.company_id == company_id

def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Dependency que extrai e valida o usuário do token JWT"""
    try:
        payload = decode_access_token(token)
        return CurrentUser(
            id_user=payload["id_user"],
            email=payload["email"],
            username=payload["username"],
            role=payload["role"],
            company_id=payload["company_id"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(min_role: str):
    """Dependency factory que requer um role mínimo"""
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_role(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {min_role} or higher"
            )
        return current_user
    return role_checker

def require_superadmin():
    """Dependency que requer role de superadmin"""
    return require_role("superadmin")

def require_admin():
    """Dependency que requer role de admin ou superior"""
    return require_role("admin")

def require_permission(permission_key: str):
    """Dependency factory que verifica se o usuário tem uma permissão específica"""
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> CurrentUser:
        # Superadmin bypassa todas as verificações de permissão
        if current_user.is_superadmin():
            return current_user
        
        # Admin também tem acesso às funcionalidades de gerenciamento
        if current_user.role == 'admin':
            return current_user
        
        # Verifica se o usuário tem a permissão específica
        user_permission = db.query(db_models.UserPermission).join(
            db_models.Permission,
            db_models.UserPermission.permission_id == db_models.Permission.id_permission
        ).filter(
            db_models.UserPermission.user_id == current_user.id_user,
            db_models.Permission.name == permission_key
        ).first()
        
        if not user_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {permission_key}"
            )
        
        return current_user
    return permission_checker

def require_same_company():
    """Dependency que garante que operações sejam limitadas à empresa do usuário"""
    def company_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        # Superadmin bypassa verificação de empresa
        if current_user.is_superadmin():
            return current_user
        
        if not current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be associated with a company"
            )
        
        return current_user
    return company_checker

def can_manage_user(target_user_id: int, db, current_user: CurrentUser) -> bool:
    """Verifica se o usuário atual pode gerenciar o usuário alvo"""
    # Superadmin pode gerenciar qualquer usuário
    if current_user.is_superadmin():
        return True
    
    # Admin só pode gerenciar usuários da mesma empresa
    if current_user.is_admin():
        target_user = db.query(db_models.User).filter(
            db_models.User.id_user == target_user_id
        ).first()
        
        if not target_user:
            return False
            
        return current_user.company_id == target_user.company_id
    
    # Usuários comuns não podem gerenciar outros usuários
    return False

def filter_users_by_company(query, current_user: CurrentUser):
    """Filtra usuários baseado na empresa do usuário atual"""
    if current_user.is_superadmin():
        return query  # Superadmin vê todos os usuários
    
    return query.filter(db_models.User.company_id == current_user.company_id)
