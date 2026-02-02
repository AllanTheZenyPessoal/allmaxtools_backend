from fastapi import HTTPException, status 
from database import db_models
from passlib.context import CryptContext
from datetime import timedelta
from token_utils.apikey_generator import create_access_token

# Configuração para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Gera hash da senha"""
    return pwd_context.hash(password)

async def readUser(user_id, db):  
    try:
        user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")   
 
async def readUsers(db):
    try:
        users = db.query(db_models.User).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
     
async def createUser(user, db): 
    try:  
        db_user = db.query(db_models.User).filter(db_models.User.email == user.email).first()
        if db_user is not None:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user = db.query(db_models.User).filter(db_models.User.username == user.username).first()
        if db_user is not None:
            raise HTTPException(status_code=400, detail="Username already registered")        

        user_data = user.model_dump()
        # Hash da senha antes de salvar
        user_data["password"] = get_password_hash(user_data["password"])
        user_data["active"] = True  #Por padrao ativa o usuario logo no cadastro  
        
        # Set default role if not provided
        if "role" not in user_data or user_data["role"] is None:
            user_data["role"] = "user"
        
        # Remove id_address if present since it's not available in the current database model
        if "id_address" in user_data:
            del user_data["id_address"]
            
        db_user = db_models.User(**user_data)  
        db.add(db_user)
        db.commit()   
        db.refresh(db_user)
        return {"message": "User created successfully", "user_id": db_user.id_user}
    
    except HTTPException:
        # Propaga HTTPException como está
        raise
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of exception
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        
async def updateUser(user_id, user, db):
    try:
        update_data = {}

        # Prepara as colunas que devem ser atualizadas
        if user.username is not None:
            update_data["username"] = user.username
            db_user = db.query(db_models.User).filter(db_models.User.username == user.username, db_models.User.id_user != user_id).first()
            if db_user is not None:
                raise HTTPException(status_code=400, detail="Username already registered")
        if user.email is not None:
            update_data["email"] = user.email
            db_user = db.query(db_models.User).filter(db_models.User.email == user.email, db_models.User.id_user != user_id).first()
            if db_user is not None:
                raise HTTPException(status_code=400, detail="Email already registered")
            
        if user.phone is not None:
            update_data["phone"] = user.phone
        if user.password is not None:
            update_data["password"] = get_password_hash(user.password)  # Hash password on update too
        if hasattr(user, 'active') and user.active is not None:
            update_data["active"] = user.active
        # id_address is not available in the current database model, so we skip it
        if user.token is not None:
            update_data["token"] = user.token
            db_user = db.query(db_models.User).filter(db_models.User.token == user.token, db_models.User.id_user != user_id).first()
            if db_user is not None:
                raise HTTPException(status_code=400, detail="Token already registered")                
         
        # Se houver algo a ser atualizado
        if update_data:
            # Atualiza as colunas relevantes
            db.query(db_models.User).filter(db_models.User.id_user == user_id).update(update_data)
            db.commit()
        
        # Retorna o usuário atualizado
        db_user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        return db_user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
         
async def deleteUser(user_id, db):
    
    try:
        db_user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(db_user)
        db.commit()    
        return {"message": "User deleted successfully", "deleted_user_id": db_user.id_user}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")  
  
async def checkLogin(user, db):     
    try:  
        db_user = db.query(db_models.User).filter(db_models.User.email == user.email).first()
           
        if db_user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Para superadmin, usar comparação direta, para outros usar hash
        # if db_user.username == 'superadmin':
        #     if user.password != db_user.password:
        #         raise HTTPException(status_code=401, detail="Invalid email or password")
        # else:
        if not verify_password(user.password, db_user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not db_user.active:
            raise HTTPException(status_code=403, detail="User account is disabled")
            
        # Gerar token JWT com role e company_id
        access_token_expires = timedelta(minutes=120)
        access_token = create_access_token(
            email=db_user.email,
            username=db_user.username,
            id_user=db_user.id_user,
            role=getattr(db_user, 'role', 'user'),  # Usar role do banco ou 'user' como padrão
            company_id=getattr(db_user, 'company_id', None),  # Usar company_id do banco
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id_user": db_user.id_user,
                "username": db_user.username,
                "email": db_user.email,
                "role": getattr(db_user, 'role', 'user'),
                "company_id": getattr(db_user, 'company_id', None)
            }
        }
    
    except HTTPException:
        # Não mascarar exceptions HTTP; repassar com o status apropriado
        raise
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

