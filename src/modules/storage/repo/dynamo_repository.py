from typing import Dict, List, Optional, Any
import logging


from src.shared.infra.repo.dynamo_repository_interface import DynamoRepositoryInterface
from src.shared.infra.external.dynamo.dynamo_client import DynamoClient
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import ProcessingResult
from src.shared.domain.entities.combined_result import CombinedResult

logger = logging.getLogger(__name__)

class DynamoRepository(DynamoRepositoryInterface):
    """Implementação do repositório do DynamoDB."""
    
    def __init__(self, dynamo_client: Optional[DynamoClient] = None):
        """
        Inicializa o repositório do DynamoDB.
        
        Args:
            dynamo_client: Cliente DynamoDB opcional. Se não fornecido, um novo cliente será criado.
        """
        self.dynamo_client = dynamo_client or DynamoClient()
    
    async def save_image_metadata(self, image: Image) -> Dict[str, Any]:
        """
        Salva os metadados de uma imagem no DynamoDB.
        
        Args:
            image: Entidade de imagem com URL e metadados
            
        Returns:
            Dict: Dados salvos no banco
        """
        try:
            item = image.to_dict()
            item["pk"] = f"IMG#{image.image_id}"
            item["sk"] = f"META#{image.image_id}"
            item["entity_type"] = "IMAGE"
            item["user_id"] = image.user_id
            
            logger.info(f"Salvando metadados da imagem {image.image_id} no DynamoDB")
            return await self.dynamo_client.put_item(item)
        
        except Exception as e:
            logger.exception(f"Erro ao salvar metadados da imagem no DynamoDB: {e}")
            raise
    
    async def save_processing_result(self, result: ProcessingResult) -> Dict[str, Any]:
        """
        Salva o resultado de um processamento no DynamoDB.
        
        Args:
            result: Resultado do processamento de imagem
            
        Returns:
            Dict: Dados salvos no banco
        """
        try:
            item = result.to_dict()
            item["pk"] = f"IMG#{result.image_id}"
            item["sk"] = f"RESULT#{result.request_id}"
            item["entity_type"] = "RESULT"
            item["model_type"] = result.model_type.value
            
            logger.info(f"Salvando resultado de processamento {result.request_id} no DynamoDB")
            return await self.dynamo_client.put_item(item)
        
        except Exception as e:
            logger.exception(f"Erro ao salvar resultado de processamento no DynamoDB: {e}")
            raise
    
    async def get_image_by_id(self, image_id: str) -> Optional[Image]:
        """
        Recupera os metadados de uma imagem pelo ID.
        
        Args:
            image_id: ID da imagem
            
        Returns:
            Optional[Image]: Entidade de imagem, se encontrada
        """
        try:
            key = {
                "pk": f"IMG#{image_id}",
                "sk": f"META#{image_id}"
            }
            
            item = await self.dynamo_client.get_item(key)
            
            if not item:
                logger.warning(f"Imagem não encontrada: {image_id}")
                return None
            
            return Image.from_dict(item)
        
        except Exception as e:
            logger.exception(f"Erro ao recuperar imagem do DynamoDB: {e}")
            raise
    
    async def get_result_by_request_id(self, request_id: str) -> Optional[ProcessingResult]:
        """
        Recupera um resultado de processamento pelo ID da requisição.
        
        Args:
            request_id: ID da requisição de processamento
            
        Returns:
            Optional[ProcessingResult]: Resultado do processamento, se encontrado
        """
        try:
            items = await self.dynamo_client.query_items(
                key_name="request_id",
                key_value=request_id,
                index_name="RequestIdIndex"
            )
            
            if not items or len(items) == 0:
                logger.warning(f"Resultado não encontrado para request_id: {request_id}")
                return None
            
            return ProcessingResult.from_dict(items[0])
        
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultado por request_id do DynamoDB: {e}")
            raise
    
    async def get_results_by_image_id(self, image_id: str) -> List[ProcessingResult]:
        """
        Recupera todos os resultados de processamento para uma imagem.
        
        Args:
            image_id: ID da imagem
            
        Returns:
            List[ProcessingResult]: Lista de resultados de processamento
        """
        try:
            items = await self.dynamo_client.query_items(
                key_name="pk",
                key_value=f"IMG#{image_id}"
            )
            
            results = []
            for item in items:
                if item.get("entity_type") == "RESULT":
                    results.append(ProcessingResult.from_dict(item))
            
            return results
        
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados por image_id do DynamoDB: {e}")
            raise
    
    async def get_results_by_user_id(self, user_id: str, limit: int = 10) -> List[ProcessingResult]:
        """
        Recupera os resultados de processamento para um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de resultados a retornar
            
        Returns:
            List[ProcessingResult]: Lista de resultados de processamento
        """
        try:
            items = await self.dynamo_client.query_items(
                key_name="user_id",
                key_value=user_id,
                index_name="UserIdIndex"
            )
            
            results = []
            for item in items:
                if item.get("entity_type") == "RESULT":
                    results.append(ProcessingResult.from_dict(item))
                    
                    if len(results) >= limit:
                        break
            
            return results
        
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados por user_id do DynamoDB: {e}")
    async def save_combined_result(self, combined_result: CombinedResult) -> Dict[str, Any]:
        """
        Salva o resultado combinado no DynamoDB.
        
        Args:
            combined_result: Resultado combinado
            
        Returns:
            Dict[str, Any]: Dados salvos no banco
        """
        try:
            item = combined_result.to_dict()
            
            logger.info(f"Salvando resultado combinado para imagem {combined_result.image_id} no DynamoDB")
            return await self.dynamo_client.put_item(item)
        
        except Exception as e:
            logger.exception(f"Erro ao salvar resultado combinado no DynamoDB: {e}")
            raise
            
    async def get_combined_result(self, image_id: str) -> Optional[CombinedResult]:
        """
        Recupera o resultado combinado pelo ID da imagem.
        
        Args:
            image_id: ID da imagem
            
        Returns:
            Optional[CombinedResult]: Resultado combinado, se encontrado
        """
        try:
            key = {
                "pk": f"IMG#{image_id}",
                "sk": "RESULT#COMBINED"
            }
            
            item = await self.dynamo_client.get_item(key)
            
            if not item:
                logger.warning(f"Resultado combinado não encontrado para image_id: {image_id}")
                return None
            
            return CombinedResult.from_dict(item)
        
        except Exception as e:
            logger.exception(f"Erro ao recuperar resultado combinado do DynamoDB: {e}")
            raise