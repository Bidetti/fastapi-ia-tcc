from typing import Dict, List, Optional, Any
import logging

from ....shared.domain.entities.result import ProcessingResult
from ...storage.repo.dynamo_repository import DynamoRepository

logger = logging.getLogger(__name__)

class GetResultUseCase:
    """Caso de uso para recuperação de resultados de processamento."""
    
    def __init__(self, dynamo_repository: Optional[DynamoRepository] = None):
        """
        Inicializa o caso de uso de recuperação de resultados.
        
        Args:
            dynamo_repository: Repositório DynamoDB opcional. Se não fornecido, um novo será criado.
        """
        self.dynamo_repository = dynamo_repository or DynamoRepository()
    
    async def get_by_request_id(self, request_id: str) -> Optional[ProcessingResult]:
        """
        Recupera um resultado de processamento pelo ID da requisição.
        
        Args:
            request_id: ID da requisição de processamento
            
        Returns:
            Optional[ProcessingResult]: Resultado do processamento, se encontrado
        """
        try:
            logger.info(f"Recuperando resultado para request_id: {request_id}")
            return await self.dynamo_repository.get_result_by_request_id(request_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultado por request_id: {e}")
            raise
    
    async def get_by_image_id(self, image_id: str) -> List[ProcessingResult]:
        """
        Recupera todos os resultados de processamento para uma imagem.
        
        Args:
            image_id: ID da imagem
            
        Returns:
            List[ProcessingResult]: Lista de resultados de processamento
        """
        try:
            logger.info(f"Recuperando resultados para image_id: {image_id}")
            return await self.dynamo_repository.get_results_by_image_id(image_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados por image_id: {e}")
            raise
    
    async def get_by_user_id(self, user_id: str, limit: int = 10) -> List[ProcessingResult]:
        """
        Recupera os resultados de processamento para um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de resultados a retornar
            
        Returns:
            List[ProcessingResult]: Lista de resultados de processamento
        """
        try:
            logger.info(f"Recuperando resultados para user_id: {user_id}")
            return await self.dynamo_repository.get_results_by_user_id(user_id, limit)
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados por user_id: {e}")
            raise