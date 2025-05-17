from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from src.shared.domain.enums.ia_model_type_enum import ModelType
from src.shared.domain.models.monitoring_models import (
    CaptureResultResponse,
    CaptureUpdateRequest,
    MonitoringMetadata,
    MonitoringSessionRequest,
    MonitoringSessionResponse,
    WebSocketConfigRequest,
)

__all__ = [
    "ImageMetadata",
    "ProcessImageRequest",
    "BoundingBox",
    "MaturationInfo",
    "DetectionInfo",
    "ProcessingSummary",
    "ProcessingResponse",
    "PresignedUrlRequest",
    "PresignedUrlResponse",
    "ProcessingStatusResponse",
    "MonitoringSessionRequest",
    "MonitoringSessionResponse",
    "CaptureResultResponse",
    "CaptureUpdateRequest",
    "WebSocketConfigRequest",
    "MonitoringMetadata",
]


class ImageMetadata(BaseModel):
    """Metadados da imagem enviada pelo cliente."""

    device_info: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: Optional[str] = None


class ProcessImageRequest(BaseModel):
    """Modelo para solicitação de processamento de imagem."""

    image_url: HttpUrl
    user_id: str
    model_type: ModelType
    metadata: Optional[ImageMetadata] = None


class BoundingBox(BaseModel):
    """Coordenadas da caixa delimitadora."""

    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_list(cls, coords: List[float]) -> "BoundingBox":
        """Cria uma instância a partir de uma lista [x, y, width, height]."""
        return cls(x=coords[0], y=coords[1], width=coords[2], height=coords[3])


class MaturationInfo(BaseModel):
    """Informações sobre o nível de maturação."""

    score: float
    category: str
    estimated_days_until_spoilage: Optional[int] = None


class DetectionInfo(BaseModel):
    """Informação sobre um objeto detectado."""

    class_name: str
    confidence: float
    bounding_box: List[float]
    maturation_level: Optional[MaturationInfo] = None


class ProcessingSummary(BaseModel):
    """Resumo do processamento."""

    total_objects: Optional[int] = None
    detection_time_ms: Optional[int] = None
    average_maturation_score: Optional[float] = None


class ProcessingResponse(BaseModel):
    """Modelo para resposta de processamento de imagem."""

    request_id: str
    image_id: str
    model_type: str
    status: str
    processing_timestamp: datetime
    results: List[DetectionInfo]
    summary: ProcessingSummary
    image_result_url: Optional[HttpUrl] = None
    error_message: Optional[str] = None


class PresignedUrlRequest(BaseModel):
    """Modelo para solicitação de URL pré-assinada para upload."""

    filename: str
    content_type: str
    user_id: str


class PresignedUrlResponse(BaseModel):
    """Modelo para resposta com URL pré-assinada para upload."""

    upload_url: HttpUrl
    image_id: str
    expires_in_seconds: int


class ProcessingStatusResponse(BaseModel):
    """Modelo para resposta de status de processamento."""

    request_id: str
    status: str
    progress: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
