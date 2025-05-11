from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from .result import ProcessingResult, DetectionResult
from ..enums.ia_model_type_enum import ModelType

class CombinedResult:
    """Classe que representa um resultado combinado de detecção e maturação."""
    
    def __init__(
        self,
        image_id: str,
        user_id: str,
        detection_result: ProcessingResult,
        maturation_result: Optional[ProcessingResult] = None,
        location: Optional[str] = None,
        processing_timestamp: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        combined_id: Optional[str] = None
    ):
        self.image_id = image_id
        self.user_id = user_id
        self.detection_result = detection_result
        self.maturation_result = maturation_result
        self.location = location
        self.processing_timestamp = processing_timestamp or datetime.utcnow()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.combined_id = combined_id or f"combined-{uuid4()}"
        
        if maturation_result and maturation_result.status == "success":
            self.status = "completed"
        elif detection_result.status == "success":
            self.status = "detection_completed"
        else:
            self.status = "error"
        
        self.total_processing_time_ms = self._calculate_total_processing_time()
        self.results = self._merge_results()
    
    def _calculate_total_processing_time(self) -> int:
        """Calcula o tempo total de processamento."""
        detection_time = self.detection_result.summary.get("detection_time_ms", 0) 
        maturation_time = 0
        if self.maturation_result:
            maturation_time = self.maturation_result.summary.get("detection_time_ms", 0)
        return detection_time + maturation_time
    
    def _merge_results(self) -> List[Dict[str, Any]]:
        """Mescla os resultados de detecção e maturação."""
        if not self.maturation_result:
            return [r.to_dict() for r in self.detection_result.results]
        
        return [r.to_dict() for r in self.maturation_result.results]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade para dicionário."""
        result = {
            "pk": f"IMG#{self.image_id}",
            "sk": "RESULT#COMBINED",
            "entity_type": "COMBINED_RESULT",
            "combined_id": self.combined_id,
            "image_id": self.image_id,
            "user_id": self.user_id,
            "processing_timestamp": self.processing_timestamp.isoformat(),
            "detection": {
                "request_id": self.detection_result.request_id,
                "status": self.detection_result.status,
                "processing_timestamp": self.detection_result.processing_timestamp.isoformat(),
                "summary": self.detection_result.summary,
                "image_result_url": self.detection_result.image_result_url
            },
            "results": self.results,
            "total_processing_time_ms": self.total_processing_time_ms,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if self.location:
            result["location"] = self.location
            
        if self.maturation_result:
            result["maturation"] = {
                "request_id": self.maturation_result.request_id,
                "status": self.maturation_result.status,
                "processing_timestamp": self.maturation_result.processing_timestamp.isoformat(),
                "summary": self.maturation_result.summary,
                "image_result_url": self.maturation_result.image_result_url
            }
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CombinedResult":
        """Cria uma instância a partir de um dicionário."""
        pass