from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ...domain.entities.image import Image
from ...domain.entities.result import ProcessingResult
from ...domain.enums.ia_model_type_enum import ModelType


class IARepositoryInterface(ABC):
    """Interface para o repositório de IA."""

    @abstractmethod
    async def detect_objects(self, image: Image) -> ProcessingResult:
        """
        Detecta objetos em uma imagem.

        Args:
            image: Entidade de imagem com URL e metadados

        Returns:
            ProcessingResult: Resultado do processamento com detecções
        """
        pass

    @abstractmethod
    async def analyze_maturation(self, image: Image) -> ProcessingResult:
        """
        Analisa o nível de maturação em uma imagem.

        Args:
            image: Entidade de imagem com URL e metadados

        Returns:
            ProcessingResult: Resultado do processamento com dados de maturação
        """
        pass
