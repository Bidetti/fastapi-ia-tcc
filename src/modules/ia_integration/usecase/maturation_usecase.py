import logging
from typing import Any, Dict, Optional

from src.modules.ia_integration.repo.ia_repository import IARepository
from src.modules.storage.repo.dynamo_repository import DynamoRepository
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType

logger = logging.getLogger(__name__)


class MaturationUseCase:
    def __init__(
        self,
        ia_repository: Optional[IARepository] = None,
        dynamo_repository: Optional[DynamoRepository] = None,
    ):
        self.ia_repository = ia_repository or IARepository()
        self.dynamo_repository = dynamo_repository or DynamoRepository()

    async def execute(
        self, image_url: str, user_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        try:
            logger.info(f"Iniciando análise de maturação para imagem: {image_url}")
            image = Image(image_url=image_url, user_id=user_id, metadata=metadata)
            await self.dynamo_repository.save_image_metadata(image)
            result = await self.ia_repository.analyze_maturation(image)
            await self.dynamo_repository.save_processing_result(result)

            return result

        except Exception as e:
            logger.exception(f"Erro no caso de uso de maturação: {e}")

            return ProcessingResult(
                image_id=image.image_id if "image" in locals() else "unknown",
                model_type=ModelType.MATURATION,
                results=[],
                status="error",
                error_message=f"Erro interno: {str(e)}",
            )
