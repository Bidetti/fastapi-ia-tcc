from typing import Dict, Optional, Any, BinaryIO
from datetime import timedelta
import logging

from src.shared.domain.entities.image import Image
from src.modules.storage.repo.s3_repository import S3Repository
from src.modules.storage.repo.dynamo_repository import DynamoRepository

logger = logging.getLogger(__name__)


class ImageUploadUseCase:
    """Caso de uso para upload de imagens."""

    def __init__(
        self,
        s3_repository: Optional[S3Repository] = None,
        dynamo_repository: Optional[DynamoRepository] = None,
    ):
        """
        Inicializa o caso de uso de upload de imagens.

        Args:
            s3_repository: Repositório S3 opcional. Se não fornecido, um novo será criado.
            dynamo_repository: Repositório DynamoDB opcional. Se não fornecido, um novo será criado.
        """
        self.s3_repository = s3_repository or S3Repository()
        self.dynamo_repository = dynamo_repository or DynamoRepository()

    async def generate_presigned_url(
        self, filename: str, content_type: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Gera uma URL pré-assinada para upload direto para o S3.

        Args:
            filename: Nome original do arquivo
            content_type: Tipo de conteúdo do arquivo
            user_id: ID do usuário

        Returns:
            Dict: Dados da URL pré-assinada, incluindo a URL e o ID da imagem
        """
        try:
            key = await self.s3_repository.generate_image_key(filename, user_id)
            presigned_url_data = await self.s3_repository.generate_presigned_url(
                key=key, content_type=content_type, expires_in=timedelta(minutes=15)
            )

            image_id = key.split("/")[-1].split(".")[0]
            response = {
                "upload_url": presigned_url_data["upload_url"],
                "image_id": image_id,
                "expires_in_seconds": presigned_url_data["expires_in_seconds"],
                "key": key,
            }

            logger.info(f"URL pré-assinada gerada para upload de imagem: {image_id}")
            return response

        except Exception as e:
            logger.exception(f"Erro ao gerar URL pré-assinada: {e}")
            raise

    async def upload_image(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Image:
        """
        Faz upload de uma imagem para o S3 e salva os metadados no DynamoDB.

        Args:
            file_obj: Objeto do arquivo
            filename: Nome original do arquivo
            user_id: ID do usuário
            content_type: Tipo de conteúdo do arquivo
            metadata: Metadados adicionais para a imagem

        Returns:
            Image: Entidade de imagem criada
        """
        try:
            key = await self.s3_repository.generate_image_key(filename, user_id)
            image_url = await self.s3_repository.upload_file(
                file_obj=file_obj,
                key=key,
                content_type=content_type,
                metadata={
                    "user_id": user_id,
                    "original_filename": filename,
                    **(metadata or {}),
                },
            )

            image = Image(
                image_url=image_url,
                user_id=user_id,
                metadata={
                    "original_filename": filename,
                    "content_type": content_type,
                    **(metadata or {}),
                },
            )

            await self.dynamo_repository.save_image_metadata(image)

            logger.info(f"Imagem {image.image_id} enviada com sucesso")
            return image

        except Exception as e:
            logger.exception(f"Erro ao fazer upload de imagem: {e}")
            raise
