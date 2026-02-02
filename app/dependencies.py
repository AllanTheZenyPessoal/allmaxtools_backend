from fastapi import Depends 
from sqlalchemy.orm import Session
from typing import Annotated
from database.database import get_session_local


# Função para obter uma sessão do banco de dados (LAZY - não conecta no import)
def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]