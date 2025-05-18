import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.modules.monitoring.repo.monitoring_repository import MonitoringRepository
from src.shared.domain.entities.monitoring_session import MonitoringSession

logger = logging.getLogger(__name__)


class MonitoringSetupUseCase:
    def __init__(self, monitoring_repository: Optional[MonitoringRepository] = None):
        self.monitoring_repository = monitoring_repository or MonitoringRepository()

    async def create_session(
        self, station_id: str, user_id: str, interval_minutes: int = 5, metadata: Optional[Dict[str, Any]] = None
    ) -> MonitoringSession:
        try:
            logger.info(f"Criando sessão de monitoramento para estação {station_id}")
            existing_session = await self.monitoring_repository.get_active_session_by_station(station_id)

            if existing_session:
                existing_session.active = False
                existing_session.end_time = datetime.now()
                await self.monitoring_repository.update_monitoring_session(existing_session)
                logger.info(f"Sessão existente {existing_session.session_id} encerrada")

            session = MonitoringSession(
                station_id=station_id, user_id=user_id, interval_minutes=interval_minutes, metadata=metadata or {}
            )

            await self.monitoring_repository.save_monitoring_session(session)
            logger.info(f"Nova sessão de monitoramento criada: {session.session_id}")

            return session

        except Exception as e:
            logger.exception(f"Erro ao criar sessão de monitoramento: {e}")
            raise

    async def update_session(
        self,
        session_id: str,
        station_id: str,
        interval_minutes: Optional[int] = None,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MonitoringSession]:
        try:
            session = await self.monitoring_repository.get_session_by_id(station_id, session_id)

            if not session:
                logger.warning(f"Sessão {session_id} não encontrada para atualização")
                return None

            if interval_minutes is not None:
                session.interval_minutes = interval_minutes

            if active is not None:
                if session.active and not active:
                    session.end_time = datetime.now()
                session.active = active

            if metadata:
                session.metadata.update(metadata)

            await self.monitoring_repository.update_monitoring_session(session)
            logger.info(f"Sessão {session_id} atualizada")

            return session

        except Exception as e:
            logger.exception(f"Erro ao atualizar sessão de monitoramento: {e}")
            raise

    async def get_session(self, station_id: str, session_id: str) -> Optional[MonitoringSession]:
        try:
            return await self.monitoring_repository.get_session_by_id(station_id, session_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar sessão de monitoramento: {e}")
            raise

    async def get_active_session(self, station_id: str) -> Optional[MonitoringSession]:
        try:
            return await self.monitoring_repository.get_active_session_by_station(station_id)
        except Exception as e:
            logger.exception(f"Erro ao recuperar sessão ativa para estação {station_id}: {e}")
            raise

    async def stop_session(self, station_id: str, session_id: str) -> bool:
        try:
            session = await self.monitoring_repository.get_session_by_id(station_id, session_id)

            if not session:
                logger.warning(f"Sessão {session_id} não encontrada para encerramento")
                return False
            session.active = False
            session.end_time = datetime.now()

            await self.monitoring_repository.update_monitoring_session(session)
            logger.info(f"Sessão {session_id} encerrada")

            return True

        except Exception as e:
            logger.exception(f"Erro ao encerrar sessão de monitoramento: {e}")
            return False
