from fastapi import FastAPI, Depends 
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import timedelta 
from database import db_models
from database.database import engine, SessionLocal
  
# Criação das tabelas do banco de dados
db_models.Base.metadata.create_all(bind=engine)

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

  