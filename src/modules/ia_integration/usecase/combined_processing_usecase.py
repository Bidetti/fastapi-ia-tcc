import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.modules.ia_integration.repo.ia_repository import IARepository
from src.modules.storage.repo.dynamo_repository import DynamoRepository
from src.shared.domain.entities.combined_result import CombinedResult
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType
from src.shared.domain.models.http_models import ProcessingStatusResponse

logger = logging.getLogger(__name__)

# Armazenamento temporário para status dos processamentos em andamento
PROCESSING_STATUS = {}


class CombinedProcessingUseCase:

    def __init__(
        self,
        ia_repository: Optional[IARepository] = None,
        dynamo_repository: Optional[DynamoRepository] = None,
    ):
        self.ia_repository = ia_repository or IARepository()
        self.dynamo_repository = dynamo_repository or DynamoRepository()

    async def start_processing(
        self,
        image_url: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        maturation_threshold: float = 0.6,
        skip_maturation: bool = False,
        location: Optional[str] = None,
    ) -> str:
        request_id = f"combined-{uuid.uuid4()}"

        PROCESSING_STATUS[request_id] = {
            "status": "queued",
            "image_url": image_url,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "progress": 0.0,
            "skip_maturation": skip_maturation,
            "image_id": None,
            "detection_complete": False,
            "maturation_complete": False,
            "combined_id": None,
            "error": None,
        }

        logger.info(f"Processamento combinado iniciado: {request_id} para imagem {image_url}")

        return request_id

    async def execute_in_background(
        self,
        request_id: str,
        image_url: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        maturation_threshold: float = 0.6,
        skip_maturation: bool = False,
        location: Optional[str] = None,
    ) -> None:
        try:
            if request_id not in PROCESSING_STATUS:
                logger.error(f"ID de solicitação não encontrado: {request_id}")
                return

            self._update_processing_status(request_id, status="processing", progress=0.1)

            image = Image(image_url=image_url, user_id=user_id, metadata=metadata)
            await self.dynamo_repository.save_image_metadata(image)

            self._update_processing_status(request_id, image_id=image.image_id, progress=0.2)

            self._update_processing_status(request_id, status="detecting", progress=0.3)
            detection_result = await self.ia_repository.detect_objects(image)
            await self.dynamo_repository.save_processing_result(detection_result)

            self._update_processing_status(
                request_id,
                detection_complete=True,
                progress=0.5,
                status="detection_complete" if skip_maturation else "detecting_maturation",
            )

            if detection_result.status != "success" or not detection_result.results:
                logger.warning(f"Falha na detecção para imagem {image.image_id}: {detection_result.error_message}")
                combined_result = CombinedResult(
                    image_id=image.image_id, user_id=user_id, detection_result=detection_result, location=location
                )

                await self.dynamo_repository.save_combined_result(combined_result)

                self._update_processing_status(
                    request_id,
                    status="completed",
                    progress=1.0,
                    combined_id=combined_result.combined_id,
                    error=detection_result.error_message,
                )

                return

            maturation_result = None
            if not skip_maturation and detection_result.results:
                valid_objects = [r for r in detection_result.results if r.confidence >= maturation_threshold]

                if valid_objects:
                    logger.info(
                        f"Realizando análise de maturação para imagem {image.image_id} "
                        f"com {len(valid_objects)} objetos válidos"
                    )
                    self._update_processing_status(request_id, progress=0.6)

                    bounding_boxes = []
                    for i, result in enumerate(valid_objects):
                        bounding_boxes.append(
                            {
                                "index": i,
                                "class_name": result.class_name,
                                "confidence": result.confidence,
                                "bounding_box": result.bounding_box,
                            }
                        )

                    maturation_result = await self.ia_repository.analyze_maturation_with_boxes(
                        image=image, bounding_boxes=bounding_boxes, parent_request_id=detection_result.request_id
                    )

                    await self.dynamo_repository.save_processing_result(maturation_result)
                    self._update_processing_status(request_id, maturation_complete=True, progress=0.8)
                else:
                    logger.info(
                        f"Nenhum objeto com confiança suficiente para análise de maturação na imagem {image.image_id}"
                    )

            combined_result = CombinedResult(
                image_id=image.image_id,
                user_id=user_id,
                detection_result=detection_result,
                maturation_result=maturation_result,
                location=location,
            )

            await self.dynamo_repository.save_combined_result(combined_result)

            self._update_processing_status(
                request_id, status="completed", progress=1.0, combined_id=combined_result.combined_id
            )

            logger.info(f"Processamento combinado concluído: {request_id} para imagem {image.image_id}")

        except Exception as e:
            logger.exception(f"Erro no processamento combinado em background: {e}")

            self._update_processing_status(request_id, status="error", progress=1.0, error=str(e))

    async def execute(
        self,
        image_url: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        maturation_threshold: float = 0.6,
        skip_maturation: bool = False,
        location: Optional[str] = None,
    ) -> CombinedResult:
        try:
            logger.info(f"Iniciando processamento combinado para imagem: {image_url}")

            image = Image(image_url=image_url, user_id=user_id, metadata=metadata)
            await self.dynamo_repository.save_image_metadata(image)

            detection_result = await self.ia_repository.detect_objects(image)
            await self.dynamo_repository.save_processing_result(detection_result)

            if detection_result.status != "success" or not detection_result.results:
                logger.warning(f"Falha na detecção para imagem {image.image_id}: {detection_result.error_message}")
                return CombinedResult(
                    image_id=image.image_id, user_id=user_id, detection_result=detection_result, location=location
                )

            maturation_result = None
            if not skip_maturation and detection_result.results:
                valid_objects = [r for r in detection_result.results if r.confidence >= maturation_threshold]

                if valid_objects:
                    logger.info(
                        f"Realizando análise de maturação para imagem {image.image_id} "
                        f"com {len(valid_objects)} objetos válidos"
                    )

                    bounding_boxes = []
                    for i, result in enumerate(valid_objects):
                        bounding_boxes.append(
                            {
                                "index": i,
                                "class_name": result.class_name,
                                "confidence": result.confidence,
                                "bounding_box": result.bounding_box,
                            }
                        )

                    maturation_result = await self.ia_repository.analyze_maturation_with_boxes(
                        image=image, bounding_boxes=bounding_boxes, parent_request_id=detection_result.request_id
                    )

                    await self.dynamo_repository.save_processing_result(maturation_result)
                else:
                    logger.info(
                        f"Nenhum objeto com confiança suficiente para análise de maturação na imagem {image.image_id}"
                    )

            combined_result = CombinedResult(
                image_id=image.image_id,
                user_id=user_id,
                detection_result=detection_result,
                maturation_result=maturation_result,
                location=location,
            )

            await self.dynamo_repository.save_combined_result(combined_result)

            return combined_result

        except Exception as e:
            logger.exception(f"Erro no caso de uso de processamento combinado: {e}")

            if "image" in locals():
                return CombinedResult(
                    image_id=image.image_id,
                    user_id=user_id,
                    detection_result=ProcessingResult(
                        image_id=image.image_id,
                        model_type=ModelType.DETECTION,
                        results=[],
                        status="error",
                        error_message=f"Erro interno: {str(e)}",
                    ),
                    location=location,
                )
            raise

    async def get_combined_result(self, image_id: str) -> Optional[CombinedResult]:
        try:
            return await self.dynamo_repository.get_combined_result(image_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultado combinado para imagem {image_id}: {e}")
            raise

    async def get_result_by_request_id(self, request_id: str) -> Optional[CombinedResult]:
        if request_id not in PROCESSING_STATUS:
            return None

        status_data = PROCESSING_STATUS[request_id]
        if status_data.get("status") != "completed":
            return None

        combined_id = status_data.get("combined_id")
        if combined_id:
            image_id = status_data.get("image_id")
            if image_id:
                return await self.get_combined_result(image_id)

        return None

    async def get_processing_status(self, request_id: str) -> Optional[ProcessingStatusResponse]:
        if request_id not in PROCESSING_STATUS:
            return None

        status_data = PROCESSING_STATUS[request_id]

        return ProcessingStatusResponse(
            request_id=request_id,
            status=status_data.get("status", "unknown"),
            progress=status_data.get("progress", 0.0),
            estimated_completion_time=None,
        )

    def _update_processing_status(self, request_id: str, **kwargs):
        if request_id in PROCESSING_STATUS:
            PROCESSING_STATUS[request_id].update(kwargs)
            PROCESSING_STATUS[request_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
