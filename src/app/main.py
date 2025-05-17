from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.app.config import settings
from src.modules.ia_integration.controller.ia_controller import ia_router
from src.modules.storage.controller.storage_controller import storage_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
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
    lifespan=lifespan,
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ia_router)
app.include_router(storage_router)


@app.get("/health-check", tags=["Health"])
async def health_check():
    """Endpoint para verificar a saúde da API."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": app.version,
    }


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz para teste."""
    return {
        "message": "API de IA para Detecção e Maturação de Frutas",
        "docs": "/docs",
        "health": "/health-check",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
