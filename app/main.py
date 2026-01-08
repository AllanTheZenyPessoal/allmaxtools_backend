from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db_models
from database.database import engine

# Import all routes
from routes import (
    address, branch, businnesspartner, company, 
    freight, paymentmethod, paymentterms, salesorder, 
    user, utilization, sincronization
)

from token_utils.token_route import router as token_router

# Create FastAPI app
app = FastAPI(
    title="Prototype API",
    description="This is a prototype API",
    version="1.0.0"
)

# Set CORS
origins = [
    "*",
    "http://localhost:3000",
    "http://localhost:4200",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Create database tables
db_models.Base.metadata.create_all(bind=engine)

# Include all routers
app.include_router(token_router)
app.include_router(address.router)
app.include_router(branch.router)
app.include_router(businnesspartner.router)
app.include_router(company.router)
app.include_router(freight.router)
app.include_router(paymentmethod.router)
app.include_router(paymentterms.router)
app.include_router(salesorder.router)
app.include_router(user.router)
app.include_router(utilization.router)
app.include_router(sincronization.router)

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
    return {
        "environment": "development",
        "version": "1.0.0",
        "auth_required": False,  # Em desenvolvimento, autenticação é opcional
        "cors_enabled": True,
        "database": "sqlite" if "sqlite" in str(engine.url) else "mysql",
        "endpoints": {
            "token_generate": "/token_generate/",
            "docs": "/docs",
            "health": "/health"
        }
    }
