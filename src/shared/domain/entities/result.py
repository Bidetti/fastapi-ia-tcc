from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import uuid4
from ..enums.ia_model_type_enum import ModelType


class DetectionResult:
    """Classe que representa o resultado de uma detecção de objeto."""
    
    def __init__(
        self,
        class_name: str,
        confidence: float,
        bounding_box: List[float],
        maturation_level: Optional[Dict[str, Any]] = None
    ):
        self.class_name = class_name
        self.confidence = confidence
        self.bounding_box = bounding_box  # [x, y, width, height] normalizado de 0 a 1
        self.maturation_level = maturation_level
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade para dicionário."""
        return {
            "class": self.class_name,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box,
            "maturation_level": self.maturation_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetectionResult":
        """Cria uma instância a partir de um dicionário."""
        return cls(
            class_name=data["class"],
            confidence=data["confidence"],
            bounding_box=data["bounding_box"],
            maturation_level=data.get("maturation_level")
        )


class ProcessingResult:
    """Classe que representa o resultado completo de um processamento de imagem."""
    
    def __init__(
        self,
        image_id: str,
        model_type: ModelType,
        results: List[DetectionResult],
        status: str = "success",
        request_id: Optional[str] = None,
        processing_timestamp: Optional[datetime] = None,
        summary: Optional[Dict[str, Any]] = None,
        image_result_url: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.request_id = request_id or f"req-{uuid4()}"
        self.image_id = image_id
        self.model_type = model_type
        self.results = results
        self.status = status
        self.processing_timestamp = processing_timestamp or datetime.utcnow()
        self.summary = summary or {}
        self.image_result_url = image_result_url
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade para dicionário."""
        return {
            "request_id": self.request_id,
            "image_id": self.image_id,
            "model_type": self.model_type.value,
            "results": [result.to_dict() for result in self.results],
            "status": self.status,
            "processing_timestamp": self.processing_timestamp.isoformat(),
            "summary": self.summary,
            "image_result_url": self.image_result_url,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingResult":
        """Cria uma instância a partir de um dicionário."""
        processing_timestamp = data.get("processing_timestamp")
        if processing_timestamp and isinstance(processing_timestamp, str):
            processing_timestamp = datetime.fromisoformat(processing_timestamp)
            
        results = [
            DetectionResult.from_dict(result_data) 
            for result_data in data.get("results", [])
        ]
        
        return cls(
            request_id=data.get("request_id"),
            image_id=data["image_id"],
            model_type=ModelType(data["model_type"]),
            results=results,
            status=data.get("status", "success"),
            processing_timestamp=processing_timestamp,
            summary=data.get("summary", {}),
            image_result_url=data.get("image_result_url"),
            error_message=data.get("error_message")
        )