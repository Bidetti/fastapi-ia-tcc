import logging
from typing import Any, Dict, List, Optional

from src.modules.storage.repo.dynamo_repository import DynamoRepository
from src.shared.domain.entities.monitoring_session import CaptureResult, MonitoringSession

logger = logging.getLogger(__name__)


class MonitoringRepository:
    def __init__(self, dynamo_repository: Optional[DynamoRepository] = None):
        self.dynamo_repository = dynamo_repository or DynamoRepository()

    async def save_monitoring_session(self, session: MonitoringSession) -> Dict[str, Any]:
        try:
            item = session.to_dict()
            item["pk"] = f"STATION#{session.station_id}"
            item["sk"] = f"SESSION#{session.session_id}"
            item["entity_type"] = "MONITORING_SESSION"
            item["user_id"] = session.user_id

            logger.info(f"Salvando sessão de monitoramento {session.session_id} no DynamoDB")
            return await self.dynamo_repository.dynamo_client.put_item(item)

        except Exception as e:
            logger.exception(f"Erro ao salvar sessão de monitoramento no DynamoDB: {e}")
            raise

    async def update_monitoring_session(self, session: MonitoringSession) -> Dict[str, Any]:
        try:
            key = {"pk": f"STATION#{session.station_id}", "sk": f"SESSION#{session.session_id}"}
            current_item = await self.dynamo_repository.dynamo_client.get_item(key)

            if not current_item:
                logger.warning(f"Sessão de monitoramento não encontrada: {session.session_id}")
                return await self.save_monitoring_session(session)

            item = session.to_dict()
            item["pk"] = f"STATION#{session.station_id}"
            item["sk"] = f"SESSION#{session.session_id}"
            item["entity_type"] = "MONITORING_SESSION"

            logger.info(f"Atualizando sessão de monitoramento {session.session_id} no DynamoDB")
            return await self.dynamo_repository.dynamo_client.put_item(item)

        except Exception as e:
            logger.exception(f"Erro ao atualizar sessão de monitoramento no DynamoDB: {e}")
            raise

    async def save_capture_result(
        self, station_id: str, session_id: str, capture_result: CaptureResult
    ) -> Dict[str, Any]:
        try:
            item = capture_result.to_dict()
            item["pk"] = f"SESSION#{session_id}"
            item["sk"] = f"CAPTURE#{capture_result.capture_id}"
            item["entity_type"] = "CAPTURE_RESULT"
            item["station_id"] = station_id

            logger.info(f"Salvando resultado de captura {capture_result.capture_id} no DynamoDB")
            await self._update_session_captures(station_id, session_id, capture_result.capture_id)

            return await self.dynamo_repository.dynamo_client.put_item(item)

        except Exception as e:
            logger.exception(f"Erro ao salvar resultado de captura no DynamoDB: {e}")
            raise

    async def get_session_by_id(self, station_id: str, session_id: str) -> Optional[MonitoringSession]:
        try:
            key = {"pk": f"STATION#{station_id}", "sk": f"SESSION#{session_id}"}
            item = await self.dynamo_repository.dynamo_client.get_item(key)

            if not item:
                logger.warning(f"Sessão de monitoramento não encontrada: {session_id}")
                return None

            return MonitoringSession.from_dict(item)

        except Exception as e:
            logger.exception(f"Erro ao recuperar sessão de monitoramento do DynamoDB: {e}")
            raise

    async def get_active_session_by_station(self, station_id: str) -> Optional[MonitoringSession]:
        try:
            items = await self.dynamo_repository.dynamo_client.query_items(
                key_name="pk",
                key_value=f"STATION#{station_id}",
                filter_expression="active = :active",
                expression_values={":active": True},
            )

            if not items or len(items) == 0:
                return None

            return MonitoringSession.from_dict(items[0])

        except Exception as e:
            logger.exception(f"Erro ao recuperar sessão ativa para estação {station_id}: {e}")
            raise

    async def get_capture_results(self, session_id: str) -> List[CaptureResult]:
        try:
            items = await self.dynamo_repository.dynamo_client.query_items(
                key_name="pk", key_value=f"SESSION#{session_id}"
            )

            results = []
            for item in items:
                if item.get("entity_type") == "CAPTURE_RESULT":
                    results.append(CaptureResult.from_dict(item))

            return results

        except Exception as e:
            logger.exception(f"Erro ao recuperar resultados de captura para sessão {session_id}: {e}")
            raise

    async def get_stations_with_active_sessions(self) -> List[Dict[str, Any]]:
        try:
            items = await self.dynamo_repository.dynamo_client.scan(
                filter_expression="begins_with(pk, :pk_prefix) AND active = :active",
                expression_values={":pk_prefix": "STATION#", ":active": True},
            )

            stations = []
            for item in items:
                if item.get("entity_type") == "MONITORING_SESSION" and item.get("active", False):
                    station_id = item.get("station_id")
                    stations.append(
                        {
                            "station_id": station_id,
                            "session_id": item.get("session_id"),
                            "interval_minutes": item.get("interval_minutes"),
                            "start_time": item.get("start_time"),
                            "user_id": item.get("user_id"),
                        }
                    )

            return stations

        except Exception as e:
            logger.exception(f"Erro ao recuperar estações com sessões ativas: {e}")
            raise

    async def _update_session_captures(self, station_id: str, session_id: str, capture_id: str) -> bool:
        try:
            session = await self.get_session_by_id(station_id, session_id)
            if not session:
                return False

            captures = session.captures or []
            if capture_id not in captures:
                captures.append(capture_id)
                session.captures = captures

                await self.update_monitoring_session(session)

            return True

        except Exception as e:
            logger.exception(f"Erro ao atualizar capturas da sessão {session_id}: {e}")
            return False
