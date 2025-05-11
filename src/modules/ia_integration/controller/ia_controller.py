from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from ....shared.domain.models.http_models import (
    ProcessImageRequest,
    ProcessingResponse,
    ProcessingStatusResponse
)
from ....shared.domain.enums.ia_model_type_enum import ModelType
from ..usecase.detect_usecase import DetectUseCase
from ..usecase.maturation_usecase import MaturationUseCase

ia_router = APIRouter(prefix="/ia", tags=["IA"])
def get_detect_usecase():
    return DetectUseCase()

def get_maturation_usecase():
    return MaturationUseCase()

@ia_router.post("/process", response_model=ProcessingResponse)
async def process_image(
    request: ProcessImageRequest,
    detect_usecase: DetectUseCase = Depends(get_detect_usecase),
    maturation_usecase: MaturationUseCase = Depends(get_maturation_usecase)
):
    """Processa uma imagem usando o modelo de IA selecionado."""
    try:
        if request.model_type == ModelType.DETECTION:
            result = await detect_usecase.execute(
                image_url=str(request.image_url),
                user_id=request.user_id,
                metadata=request.metadata.dict() if request.metadata else None
            )
        elif request.model_type == ModelType.MATURATION:
            result = await maturation_usecase.execute(
                image_url=str(request.image_url),
                user_id=request.user_id,
                metadata=request.metadata.dict() if request.metadata else None
            )
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de modelo inválido: {request.model_type}")
        
        response_data = result.to_dict()
        return ProcessingResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")