import aiohttp
import logging
from typing import Dict, Any, Optional
import json
from src.app.config import settings

logger = logging.getLogger(__name__)


class EC2Client:
    """Cliente para comunicação com a API de IA em EC2."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = base_url or settings.EC2_IA_ENDPOINT
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.detect_endpoint = f"{self.base_url}/detect"
        self.maturation_endpoint = f"{self.base_url}/maturation"
        logger.info(f"Inicializando cliente EC2 para endpoint {self.base_url}")

    async def _make_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Erro na resposta da API de IA: {response.status} - {error_text}"
                        )
                        return {
                            "status": "error",
                            "error_message": f"Erro {response.status}: {error_text}",
                        }

                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Erro ao conectar à API de IA: {e}")
            return {"status": "error", "error_message": f"Erro de conexão: {str(e)}"}
        except Exception as e:
            logger.error(f"Erro inesperado ao processar requisição: {e}")
            return {"status": "error", "error_message": f"Erro inesperado: {str(e)}"}

    async def detect_objects(
        self, image_url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {"image_url": image_url, "metadata": metadata or {}}

        logger.info(f"Enviando solicitação de detecção para imagem: {image_url}")
        return await self._make_request(self.detect_endpoint, payload)

    async def analyze_maturation(
        self, image_url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {"image_url": image_url, "metadata": metadata or {}}

        logger.info(
            f"Enviando solicitação de análise de maturação para imagem: {image_url}"
        )
        return await self._make_request(self.maturation_endpoint, payload)

    async def analyze_maturation_with_boxes(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/maturation-with-boxes"
        logger.info(
            f"Enviando solicitação de análise de maturação com caixas para imagem: {payload.get('image_url')}"
        )
        return await self._make_request(url, payload)
