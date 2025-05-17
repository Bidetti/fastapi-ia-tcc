from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, BinaryIO, Dict, Optional


class S3RepositoryInterface(ABC):
    """Interface para o repositório do S3."""

    @abstractmethod
    async def generate_presigned_url(
        self, key: str, content_type: str, expires_in: timedelta = timedelta(minutes=15)
    ) -> Dict[str, Any]:
        """
        Gera uma URL pré-assinada para upload direto para o S3.

        Args:
            key: Caminho do objeto no bucket
            content_type: Tipo de conteúdo do arquivo
            expires_in: Tempo de expiração da URL

        Returns:
            Dict: Dados da URL pré-assinada
        """
        pass

    @abstractmethod
    async def upload_file(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Faz upload de um arquivo para o S3.

        Args:
            file_obj: Objeto do arquivo
            key: Caminho do objeto no bucket
            content_type: Tipo de conteúdo do arquivo
            metadata: Metadados do arquivo

        Returns:
            str: URL do arquivo no S3
        """
        pass

    @abstractmethod
    async def get_file_url(self, key: str) -> str:
        """
        Obtém a URL de um arquivo no S3.

        Args:
            key: Caminho do objeto no bucket

        Returns:
            str: URL do arquivo no S3
        """
        pass

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """
        Exclui um arquivo do S3.

        Args:
            key: Caminho do objeto no bucket

        Returns:
            bool: True se a exclusão foi bem-sucedida
        """
        pass
