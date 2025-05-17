import logging
from typing import Any, Dict, List, Optional

from src.modules.monitoring.repo.monitoring_repository import MonitoringRepository
from src.shared.domain.entities.monitoring_session import CaptureResult
from src.shared.infra.websocket.websocket_manager import connection_manager

logger = logging.getLogger(__name__)


class MonitoringScheduleUseCase:
    def __init__(self, monitoring_repository: Optional[MonitoringRepository] = None):
        self.monitoring_repository = monitoring_repository or MonitoringRepository()

    async def configure_websocket(
        self, connection_id: str, station_id: str, user_id: str, interval_minutes: int = 5
    ) -> bool:
        try:
            configured = await connection_manager.configure_monitoring(
                connection_id=connection_id,
                interval_minutes=interval_minutes,
                station_id=station_id,
                user_id=user_id,
                is_active=True,
            )

            if not configured:
                logger.warning(f"Falha ao configurar WebSocket para {connection_id}")
                return False

            logger.info(f"WebSocket configurado para monitoramento: {connection_id}, estação: {station_id}")
            return True

        except Exception as e:
            logger.exception(f"Erro ao configurar monitoramento para WebSocket: {e}")
            return False

    async def start_monitoring(self, connection_id: str) -> bool:
        try:
            started = await connection_manager.start_monitoring(connection_id)

            if started:
                logger.info(f"Monitoramento iniciado para {connection_id}")
            else:
                logger.warning(f"Falha ao iniciar monitoramento para {connection_id}")

            return started

        except Exception as e:
            logger.exception(f"Erro ao iniciar monitoramento: {e}")
            return False

    async def stop_monitoring(self, connection_id: str) -> bool:
        try:
            stopped = await connection_manager.stop_monitoring(connection_id)

            if stopped:
                logger.info(f"Monitoramento parado para {connection_id}")
            else:
                logger.warning(f"Falha ao parar monitoramento para {connection_id}")

            return stopped

        except Exception as e:
            logger.exception(f"Erro ao parar monitoramento: {e}")
            return False

    async def record_capture(
        self, station_id: str, session_id: str, image_id: str, image_url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> CaptureResult:
        try:
            session = await self.monitoring_repository.get_session_by_id(station_id, session_id)

            if not session:
                logger.warning(f"Sessão {session_id} não encontrada ao registrar captura")
                raise ValueError(f"Sessão {session_id} não encontrada")

            capture_result = CaptureResult(
                image_id=image_id, image_url=image_url, status="captured", metadata=metadata or {}
            )

            await self.monitoring_repository.save_capture_result(
                station_id=station_id, session_id=session_id, capture_result=capture_result
            )

            logger.info(f"Captura registrada: {capture_result.capture_id} para sessão {session_id}")
            return capture_result

        except Exception as e:
            logger.exception(f"Erro ao registrar captura: {e}")
            raise

    async def update_capture_status(
        self,
        session_id: str,
        capture_id: str,
        status: str,
        result_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CaptureResult]:
        try:
            captures = await self.monitoring_repository.get_capture_results(session_id)

            target_capture = None
            for capture in captures:
                if capture.capture_id == capture_id:
                    target_capture = capture
                    break

            if not target_capture:
                logger.warning(f"Captura {capture_id} não encontrada para atualização")
                return None
            target_capture.status = status

            if result_ids:
                target_capture.result_ids = list(set(target_capture.result_ids + result_ids))

            if metadata:
                target_capture.metadata.update(metadata)

            session = await self.monitoring_repository.get_session_by_id(None, session_id)
            if not session:
                logger.warning(f"Sessão {session_id} não encontrada ao atualizar captura")
                return None
            await self.monitoring_repository.save_capture_result(
                station_id=session.station_id, session_id=session_id, capture_result=target_capture
            )

            logger.info(f"Captura {capture_id} atualizada para status: {status}")
            return target_capture

        except Exception as e:
            logger.exception(f"Erro ao atualizar status da captura: {e}")
            return None

    async def get_session_captures(self, session_id: str) -> List[CaptureResult]:
        try:
            return await self.monitoring_repository.get_capture_results(session_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar capturas da sessão {session_id}: {e}")
            return []
