from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ...domain.entities.image import Image
from ...domain.entities.result import ProcessingResult


class DynamoRepositoryInterface(ABC):
    """Interface para o repositório do DynamoDB."""
    
    @abstractmethod
    async def save_image_metadata(self, image: Image) -> Dict[str, Any]:
        """
        Salva os metadados de uma imagem no DynamoDB.
        
        Args:
            image: Entidade de imagem com URL e metadados
            
        Returns:
            Dict: Dados salvos no banco
        """
        pass
    
    @abstractmethod
    async def save_processing_result(self, result: ProcessingResult) -> Dict[str, Any]:
        """
        Salva o resultado de um processamento no DynamoDB.
        
        Args:
            result: Resultado do processamento de imagem
            
        Returns:
            Dict: Dados salvos no banco
        """
        pass
    
    @abstractmethod
    async def get_image_by_id(self, image_id: str) -> Optional[Image]:
        """
        Recupera os metadados de uma imagem pelo ID.
        
        Args:
            image_id: ID da imagem
            
        Returns:
            Optional[Image]: Entidade de imagem, se encontrada
        """
        pass
    
    @abstractmethod
    async def get_result_by_request_id(self, request_id: str) -> Optional[ProcessingResult]:
        """
        Recupera um resultado de processamento pelo ID da requisição.
        
        Args:
            request_id: ID da requisição de processamento
            
        Returns:
            Optional[ProcessingResult]: Resultado do processamento, se encontrado
        """
        pass
    
    @abstractmethod
    async def get_results_by_image_id(self, image_id: str) -> List[ProcessingResult]:
        """
        Recupera todos os resultados de processamento para uma imagem.
        
        Args:
            image_id: ID da imagem
            
        Returns:
            List[ProcessingResult]: Lista de resultados de processamento
        """
        pass
    
    @abstractmethod
    async def get_results_by_user_id(self, user_id: str, limit: int = 10) -> List[ProcessingResult]:
        """
        Recupera os resultados de processamento para um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de resultados a retornar
            
        Returns:
            List[ProcessingResult]: Lista de resultados de processamento
        """
        pass