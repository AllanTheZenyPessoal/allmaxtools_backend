from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
import os
import time

# MySQL database URL
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "123")
DATABASE_HOST = os.getenv("DATABASE_HOST", "prototype-mysql-1")
DATABASE_PORT = os.getenv("DATABASE_PORT", "3306")
DATABASE_NAME = os.getenv("DATABASE", "prototype")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Engine é criado LAZY - não conecta no import
engine = None
SessionLocal = None
Base = declarative_base()


def init_db(max_retries: int = 10, retry_delay: int = 3):
    """
    Inicializa conexão com o banco com retry.
    Deve ser chamado no startup do FastAPI, NÃO no import.
    """
    global engine, SessionLocal
    
    for attempt in range(max_retries):
        try:
            print(f"[DB] Tentativa {attempt + 1}/{max_retries} de conexão com MySQL...")
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                pool_pre_ping=True,  # Verifica conexão antes de usar
                echo=True  # Para debug
            )
            # Testa a conexão
            with engine.connect() as conn:
                print("[DB] ✅ Conexão com MySQL estabelecida!")
            
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return True
            
        except OperationalError as e:
            print(f"[DB] ⚠️ MySQL não pronto: {e}")
            if attempt < max_retries - 1:
                print(f"[DB] Aguardando {retry_delay}s antes do próximo retry...")
                time.sleep(retry_delay)
    
    raise RuntimeError(f"[DB] ❌ Falha ao conectar com MySQL após {max_retries} tentativas")


def get_engine():
    """Retorna o engine, garantindo que foi inicializado."""
    if engine is None:
        raise RuntimeError("Database não inicializado. Chame init_db() primeiro.")
    return engine


def get_session_local():
    """Retorna o SessionLocal, garantindo que foi inicializado."""
    if SessionLocal is None:
        raise RuntimeError("Database não inicializado. Chame init_db() primeiro.")
    return SessionLocal