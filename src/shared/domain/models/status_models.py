from typing import Any, Dict, Optional

from pydantic import BaseModel


class ServiceStatusResponse(BaseModel):
    """Modelo para resposta de status de um serviço específico."""

    service_name: str
    endpoint: str
    status: str
    message: str
    response_time_ms: int
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Modelo para resposta de verificação de saúde completa do sistema."""

    status: str
    timestamp: str
    environment: str
    version: str
    services: Dict[str, Dict[str, Any]]
    response_time_ms: int
    metrics: Optional[Dict[str, Any]] = None
