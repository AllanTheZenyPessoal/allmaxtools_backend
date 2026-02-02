from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import  OAuth2PasswordRequestForm 
from pydantic import BaseModel
from database import db_models
from token_utils.apikey_generator import create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES 
from dependencies import db_dependency

class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter(
    # prefix="/address",
    tags=["token_generate"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)

@router.post("/token_generate/", response_model=dict)
async def login_for_access_token(
    response: Response, 
    db: db_dependency,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    return await _authenticate_user(response, db, form_data.username, form_data.password)


@router.post("/token_generate_json/", response_model=dict)
async def login_for_access_token_json(
    response: Response, 
    db: db_dependency,
    login_data: LoginRequest
):
    return await _authenticate_user(response, db, login_data.username, login_data.password)


async def _authenticate_user(response: Response, db, username: str, password: str):
    # Check user credentials
    try:
        
        # Query todos os campos necessários incluindo role e company_id
        db_user = db.query(db_models.User).filter(
            db_models.User.email == username
        ).first()

        # Verificar senha - temporariamente usando texto plano para superadmin
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Incorrect email or password"
            )
 
        # Verificar senha usando hash bcrypt para todos os usuários
        from endpoint.user import verify_password
        if not verify_password(password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Incorrect email or password"
            )
        
        # Verificar se o usuário está ativo
        if db_user.active is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Generate access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            email=db_user.email,
            username=db_user.username or db_user.email.split('@')[0],
            id_user=db_user.id_user,
            role=db_user.role,
            company_id=db_user.company_id,
            expires_delta=access_token_expires
        )
        
        # Add the token to the response header
        response.headers["Authorization"] = f"Bearer {access_token}"
        
        # Return the token and its type
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Database query error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )