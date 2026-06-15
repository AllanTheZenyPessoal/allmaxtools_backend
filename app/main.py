from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db_models
from database.database import init_db, get_engine, get_session_local

# Import active routes
from routes import user, crypto, account, binance

from token_utils.token_route import router as token_router

# Create FastAPI app
app = FastAPI(
    title="AllmaxTools API",
    version="1.0.0",
    description="API para gerenciamento de trades, preços e conta de usuário em criptomoedas.",
    root_path="/api",
    openapi_tags=[
        {
            "name": "crypto",
            "description": "Preços de mercado, histórico e execução de ordens de compra/venda.",
        },
        {
            "name": "account",
            "description": "Saldo, holdings, portfólio, depósito e saque da conta do usuário.",
        },
        {
            "name": "auth",
            "description": "Geração e validação de tokens de acesso.",
        },
        {
            "name": "user",
            "description": "Gerenciamento de usuários.",
        },
        {
            "name": "binance",
            "description": (
                "Gerenciamento de credenciais Binance e verificação de saúde da conta. "
                "Os trades live com credenciais cadastradas são executados via MARKET order na Binance."
            ),
        },
    ],
)

# Set CORS
origins = [
    "*",
    # "http://localhost:3000",
    # "http://localhost:4200",
    # "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


# Startup event - inicializa DB com retry (NÃO no import!)
@app.on_event("startup")
async def startup_event():
    """
    Inicializa conexão com banco de dados no startup.
    Isso permite que o MySQL suba antes da API tentar conectar.
    """
    import os

    if os.getenv("TESTING") == "1":
        print("[API] Startup em modo de teste: init_db ignorado.")
        return

    print("[API] Iniciando conexão com banco de dados...")
    init_db()

    # Cria tabelas DEPOIS da conexão estar estabelecida
    engine = get_engine()
    db_models.Base.metadata.create_all(bind=engine)
    print("[API] ✅ Tabelas criadas/verificadas com sucesso!")

    # Auto-start price collector so history is always available
    from endpoint.crypto import crypto_collector_service
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        result = await crypto_collector_service.play(db, interval_seconds=2)
        print(f"[API] ✅ Coletor de preços: {result.get('status')}")
    except Exception as e:
        print(f"[API] ⚠️  Coletor de preços não iniciado: {e}")
    finally:
        db.close()


# Include all routers
app.include_router(token_router)
app.include_router(user.router)
app.include_router(crypto.router)
app.include_router(account.router)
app.include_router(binance.router)

@app.get("/")
async def root():
    return {"message": "Prototype API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/config")
async def get_config():
    """
    Retorna configurações da API para o frontend
    Útil para desenvolvimento
    """
    import os
    from database.database import get_engine, SQLALCHEMY_DATABASE_URL
    
    return {
        "environment": "development",
        "version": "1.0.0",
        "auth_required": False,  # Em desenvolvimento, autenticação é opcional
        "cors_enabled": True,
        "database": "sqlite" if "sqlite" in SQLALCHEMY_DATABASE_URL else "mysql",
        "endpoints": {
            "token_generate": "/token_generate/",
            "docs": "/docs",
            "health": "/health"
        }
    }
