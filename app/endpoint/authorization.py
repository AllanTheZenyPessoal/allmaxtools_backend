from fastapi import HTTPException, status
from database import db_models, base_models
from sqlalchemy.orm import Session
from typing import List

async def create_screen(screen_data: base_models.ScreenBase, db: Session):
    """Cria uma nova tela no sistema (apenas superadmin)"""
    try:
        # Verificar se já existe uma tela com o mesmo nome
        existing_screen = db.query(db_models.Screen).filter(
            db_models.Screen.name == screen_data.name
        ).first()
        
        if existing_screen:
            return HTTPException(status_code=400, detail="Screen name already exists")
        
        db_screen = db_models.Screen(**screen_data.model_dump())
        db.add(db_screen)
        db.commit()
        db.refresh(db_screen)
        
        return {"message": "Screen created successfully", "screen_id": db_screen.id_screen}
    
    except Exception as e:
        db.rollback()
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def create_permission(permission_data: base_models.PermissionBase, db: Session):
    """Cria uma nova permissão no sistema (apenas superadmin)"""
    try:
        # Verificar se já existe uma permissão com a mesma chave
        existing_permission = db.query(db_models.Permission).filter(
            db_models.Permission.key == permission_data.key
        ).first()
        
        if existing_permission:
            return HTTPException(status_code=400, detail="Permission key already exists")
        
        db_permission = db_models.Permission(**permission_data.model_dump())
        db.add(db_permission)
        db.commit()
        db.refresh(db_permission)
        
        return {"message": "Permission created successfully", "permission_id": db_permission.id_permission}
    
    except Exception as e:
        db.rollback()
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def get_screens(db: Session):
    """Lista todas as telas do sistema"""
    try:
        screens = db.query(db_models.Screen).filter(db_models.Screen.active == True).all()
        return screens
    except Exception as e:
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def get_permissions(db: Session, screen_id: int = None):
    """Lista todas as permissões do sistema, opcionalmente filtradas por tela"""
    try:
        query = db.query(db_models.Permission).filter(db_models.Permission.active == True)
        
        if screen_id:
            query = query.filter(db_models.Permission.screen_id == screen_id)
        
        permissions = query.all()
        return permissions
    except Exception as e:
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def assign_permissions_to_user(
    user_id: int, 
    permission_keys: List[str], 
    granted_by_user_id: int,
    db: Session
):
    """Atribui permissões a um usuário (apenas admin da mesma empresa)"""
    try:
        # Verificar se o usuário existe
        user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if not user:
            return HTTPException(status_code=404, detail="User not found")
        
        # Remover permissões existentes do usuário
        db.query(db_models.UserPermission).filter(
            db_models.UserPermission.user_id == user_id
        ).delete()
        
        # Adicionar novas permissões
        for permission_key in permission_keys:
            permission = db.query(db_models.Permission).filter(
                db_models.Permission.key == permission_key,
                db_models.Permission.active == True
            ).first()
            
            if permission:
                user_permission = db_models.UserPermission(
                    user_id=user_id,
                    permission_id=permission.id_permission,
                    granted_by=granted_by_user_id
                )
                db.add(user_permission)
        
        db.commit()
        return {"message": "Permissions assigned successfully", "user_id": user_id}
    
    except Exception as e:
        db.rollback()
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def get_user_permissions(user_id: int, db: Session):
    """Obtém todas as permissões de um usuário"""
    try:
        permissions = db.query(db_models.Permission).join(
            db_models.UserPermission
        ).filter(
            db_models.UserPermission.user_id == user_id,
            db_models.Permission.active == True
        ).all()
        
        return permissions
    except Exception as e:
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def create_company(company_data: base_models.CompanyBase, db: Session):
    """Cria uma nova empresa (apenas superadmin)"""
    try:
        # Verificar se já existe uma empresa com o mesmo CNPJ
        existing_company = db.query(db_models.Company).filter(
            db_models.Company.cnpj == company_data.cnpj
        ).first()
        
        if existing_company:
            return HTTPException(status_code=400, detail="CNPJ already registered")
        
        company_dict = company_data.model_dump()
        db_company = db_models.Company(**company_dict)
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        return {"message": "Company created successfully", "company_id": db_company.id_company}
    
    except Exception as e:
        db.rollback()
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def create_admin_user(user_data: base_models.UserCreateRequest, db: Session):
    """Cria um usuário admin vinculado a uma empresa (apenas superadmin)"""
    try:
        from endpoint.user import get_password_hash
        
        # Verificar se email já existe
        existing_user = db.query(db_models.User).filter(
            db_models.User.email == user_data.email
        ).first()
        
        if existing_user:
            return HTTPException(status_code=400, detail="Email already registered")
        
        # Verificar se a empresa existe
        if user_data.company_id:
            company = db.query(db_models.Company).filter(
                db_models.Company.id_company == user_data.company_id
            ).first()
            
            if not company:
                return HTTPException(status_code=404, detail="Company not found")
        
        user_dict = user_data.model_dump()
        user_dict["password"] = get_password_hash(user_dict["password"])
        user_dict["active"] = True
        
        db_user = db_models.User(**user_dict)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return {"message": "Admin user created successfully", "user_id": db_user.id_user}
    
    except Exception as e:
        db.rollback()
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
