from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando API FastAPI em AWS Lambda")
    yield
    logger.info("Encerrando API FastAPI")

app = FastAPI(
    title="IA Detector API",
    description="API para detecção e análise de maturação usando IA",
    version="0.1.0",
    lifespan=lifespan
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de rotas

@app.get("/health-check", tags=["Health"])
async def health_check():
    """Endpoint para verificar a saúde da API"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": app.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)