from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class ImageMetadata(BaseModel):
    """Metadados da imagem enviada pelo cliente."""

    device_info: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: Optional[str] = None


class MaturationInfo(BaseModel):
    """Informações sobre o nível de maturação."""

    score: float
    category: str
    estimated_days_until_spoilage: Optional[int] = None


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
