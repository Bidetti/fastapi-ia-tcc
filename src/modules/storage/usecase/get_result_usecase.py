import logging
from typing import List, Optional

from src.modules.storage.repo.dynamo_repository import DynamoRepository
from src.shared.domain.entities.result import ProcessingResult

logger = logging.getLogger(__name__)


class GetResultUseCase:
    def __init__(self, dynamo_repository: Optional[DynamoRepository] = None):
        self.dynamo_repository = dynamo_repository or DynamoRepository()

    async def get_by_request_id(self, request_id: str) -> Optional[ProcessingResult]:
        try:
            logger.info(f"Recuperando resultado para request_id: {request_id}")
            return await self.dynamo_repository.get_result_by_request_id(request_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultado por request_id: {e}")
            raise

    async def get_by_image_id(self, image_id: str) -> List[ProcessingResult]:
        try:
            logger.info(f"Recuperando resultados para image_id: {image_id}")
            return await self.dynamo_repository.get_results_by_image_id(image_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados por image_id: {e}")
            raise

    async def get_by_user_id(self, user_id: str, limit: int = 10) -> List[ProcessingResult]:
        try:
            logger.info(f"Recuperando resultados para user_id: {user_id}")
            return await self.dynamo_repository.get_results_by_user_id(user_id, limit)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados por user_id: {e}")
            raise
