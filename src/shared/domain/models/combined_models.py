from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl

from src.shared.domain.models.base_models import DetectionInfo, ImageMetadata, ProcessingSummary


class CombinedProcessingRequest(BaseModel):
    """Modelo para solicitação de processamento combinado (detecção + maturação)."""

    image_url: HttpUrl
    user_id: str
    perform_maturation: bool = True
    maturation_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Limiar de confiança para análise de maturação"
    )
    metadata: Optional[ImageMetadata] = None
    location: Optional[str] = None


class CombinedProcessingResponse(BaseModel):
    """Modelo para resposta de processamento combinado."""

    combined_id: str
    image_id: str
    user_id: str
    status: str  # "completed", "detection_completed", "error"
    total_processing_time_ms: int
    detection: Dict[str, Any]  # Inclui request_id, status, image_result_url
    maturation: Optional[Dict[str, Any]] = None
    results: List[DetectionInfo]
    location: Optional[str] = None
    processing_timestamp: str
    created_at: str
    updated_at: str
    summary: ProcessingSummary


class ProcessingConfig(BaseModel):
    """Configurações para processamento de imagens."""

    min_detection_confidence: float = Field(0.6, ge=0.0, le=1.0)
    min_maturation_confidence: float = Field(0.7, ge=0.0, le=1.0)
    enable_auto_maturation: bool = True
    max_results: int = Field(50, ge=1)
    allowed_classes: Optional[List[str]] = None
