from typing import Dict, Any, Optional, List
import logging

from src.shared.infra.repo.ia_repository_interface import IARepositoryInterface
from src.shared.infra.external.ec2.ec2_client import EC2Client
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import ProcessingResult, DetectionResult
from src.shared.domain.enums.ia_model_type_enum import ModelType

logger = logging.getLogger(__name__)


class IARepository(IARepositoryInterface):
    """Implementação do repositório de IA."""

    def __init__(self, ec2_client: Optional[EC2Client] = None):
        """
        Inicializa o repositório de IA.

        Args:
            ec2_client: Cliente EC2 opcional. Se não fornecido, um novo cliente será criado.
        """
        self.ec2_client = ec2_client or EC2Client()

    async def detect_objects(self, image: Image) -> ProcessingResult:
        """
        Detecta objetos em uma imagem.

        Args:
            image: Entidade de imagem com URL e metadados

        Returns:
            ProcessingResult: Resultado do processamento com detecções
        """
        try:
            response = await self.ec2_client.detect_objects(
                image_url=image.image_url, metadata=image.metadata
            )
            if response.get("status") == "error":
                logger.error(
                    f"Erro na detecção de objetos: {response.get('error_message')}"
                )
                return ProcessingResult(
                    image_id=image.image_id,
                    model_type=ModelType.DETECTION,
                    results=[],
                    status="error",
                    error_message=response.get(
                        "error_message", "Erro desconhecido no processamento"
                    ),
                )
            detection_results = []
            for result in response.get("results", []):
                detection_results.append(
                    DetectionResult(
                        class_name=result["class_name"],
                        confidence=result["confidence"],
                        bounding_box=result["bounding_box"],
                        maturation_level=None,  # A detecção não inclui dados de maturação
                    )
                )

            return ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.DETECTION,
                results=detection_results,
                status=response.get("status", "success"),
                request_id=response.get("request_id"),
                summary=response.get("summary", {}),
                image_result_url=response.get("image_result_url"),
            )

        except Exception as e:
            logger.exception(f"Erro ao processar detecção de objetos: {e}")
            return ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.DETECTION,
                results=[],
                status="error",
                error_message=f"Erro interno: {str(e)}",
            )

    async def analyze_maturation(self, image: Image) -> ProcessingResult:
        """
        Analisa o nível de maturação em uma imagem.

        Args:
            image: Entidade de imagem com URL e metadados

        Returns:
            ProcessingResult: Resultado do processamento com dados de maturação
        """
        try:
            response = await self.ec2_client.analyze_maturation(
                image_url=image.image_url, metadata=image.metadata
            )

            if response.get("status") == "error":
                logger.error(
                    f"Erro na análise de maturação: {response.get('error_message')}"
                )
                return ProcessingResult(
                    image_id=image.image_id,
                    model_type=ModelType.MATURATION,
                    results=[],
                    status="error",
                    error_message=response.get(
                        "error_message", "Erro desconhecido no processamento"
                    ),
                )

            detection_results = []
            for result in response.get("results", []):
                detection_results.append(
                    DetectionResult(
                        class_name=result["class_name"],
                        confidence=result["confidence"],
                        bounding_box=result["bounding_box"],
                        maturation_level=result.get("maturation_level"),
                    )
                )

            return ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.MATURATION,
                results=detection_results,
                status=response.get("status", "success"),
                request_id=response.get("request_id"),
                summary=response.get("summary", {}),
                image_result_url=response.get("image_result_url"),
            )

        except Exception as e:
            logger.exception(f"Erro ao processar análise de maturação: {e}")
            return ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.MATURATION,
                results=[],
                status="error",
                error_message=f"Erro interno: {str(e)}",
            )

    async def analyze_maturation_with_boxes(
        self,
        image: Image,
        bounding_boxes: List[Dict[str, Any]],
        parent_request_id: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Analisa o nível de maturação em uma imagem com caixas de delimitação predefinidas.

        Args:
            image: Entidade de imagem
            bounding_boxes: Lista de caixas delimitadoras com classes
            parent_request_id: ID da requisição de detecção relacionada

        Returns:
            ProcessingResult: Resultado do processamento com dados de maturação
        """
        try:
            payload = {
                "image_url": image.image_url,
                "bounding_boxes": bounding_boxes,
                "metadata": {
                    **(image.metadata or {}),
                    "detection_request_id": parent_request_id,
                },
            }
            response = await self.ec2_client.analyze_maturation_with_boxes(payload)

            detection_results = []
            for result in response.get("results", []):
                detection_results.append(
                    DetectionResult(
                        class_name=result["class_name"],
                        confidence=result["confidence"],
                        bounding_box=result["bounding_box"],
                        maturation_level=result.get("maturation_level"),
                    )
                )

            return ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.MATURATION,
                results=detection_results,
                status=response.get("status", "success"),
                request_id=response.get("request_id"),
                summary=response.get("summary", {}),
                image_result_url=response.get("image_result_url"),
                parent_request_id=parent_request_id,
            )

        except Exception as e:
            logger.exception(f"Erro ao processar análise de maturação com caixas: {e}")
            return ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.MATURATION,
                results=[],
                status="error",
                error_message=f"Erro interno: {str(e)}",
                parent_request_id=parent_request_id,
            )
