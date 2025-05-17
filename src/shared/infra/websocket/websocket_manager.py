import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_configs: Dict[str, Dict[str, Any]] = {}
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket) -> str:
        connection_id = str(uuid4())
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_configs[connection_id] = {
            "interval_minutes": 5,
            "is_active": False,
            "station_id": None,
            "user_id": None,
            "last_capture": None,
            "connected_at": datetime.now().isoformat(),
        }
        logger.info(f"Nova conexão WebSocket estabelecida: {connection_id}")
        return connection_id

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            self._cancel_scheduled_task(connection_id)
            self.active_connections.pop(connection_id)
            self.connection_configs.pop(connection_id)
            logger.info(f"Conexão WebSocket encerrada: {connection_id}")

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> bool:
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
                logger.debug(f"Mensagem enviada para {connection_id}: {message}")
                return True
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem para {connection_id}: {e}")
                return False
        return False

    async def broadcast(self, message: Dict[str, Any]):
        disconnected_ids = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar broadcast para {connection_id}: {e}")
                disconnected_ids.append(connection_id)

        for connection_id in disconnected_ids:
            self.disconnect(connection_id)

    async def configure_monitoring(
        self, connection_id: str, interval_minutes: int, station_id: str, user_id: str, is_active: bool = True
    ) -> bool:
        if connection_id not in self.active_connections:
            return False

        self._cancel_scheduled_task(connection_id)

        self.connection_configs[connection_id] = {
            "interval_minutes": interval_minutes,
            "is_active": is_active,
            "station_id": station_id,
            "user_id": user_id,
            "last_capture": None,
            "connected_at": self.connection_configs[connection_id].get("connected_at"),
        }

        if is_active:
            await self._schedule_monitoring(connection_id)
            logger.info(
                f"Monitoramento configurado para {connection_id}: intervalo={interval_minutes}min, estação={station_id}"
            )

        return True

    async def start_monitoring(self, connection_id: str) -> bool:
        if connection_id not in self.connection_configs:
            return False

        config = self.connection_configs[connection_id]

        if not config.get("station_id") or not config.get("user_id"):
            logger.warning(
                f"Monitoramento não pode ser iniciado para {connection_id}: faltam informações de estação ou usuário"
            )
            return False

        config["is_active"] = True

        await self._schedule_monitoring(connection_id)
        logger.info(f"Monitoramento iniciado para {connection_id}")

        return True

    async def stop_monitoring(self, connection_id: str) -> bool:
        if connection_id not in self.connection_configs:
            return False

        self._cancel_scheduled_task(connection_id)
        self.connection_configs[connection_id]["is_active"] = False

        logger.info(f"Monitoramento parado para {connection_id}")
        return True

    def _cancel_scheduled_task(self, connection_id: str):
        if connection_id in self.scheduled_tasks:
            task = self.scheduled_tasks[connection_id]
            if not task.done() and not task.cancelled():
                task.cancel()
            self.scheduled_tasks.pop(connection_id)

    async def _schedule_monitoring(self, connection_id: str):
        self._cancel_scheduled_task(connection_id)

        task = asyncio.create_task(self._monitor_loop(connection_id))
        self.scheduled_tasks[connection_id] = task

    async def _monitor_loop(self, connection_id: str):
        try:
            while connection_id in self.active_connections:
                config = self.connection_configs.get(connection_id)
                if not config or not config.get("is_active"):
                    break
                capture_request = {
                    "type": "capture_request",
                    "timestamp": datetime.now().isoformat(),
                    "station_id": config.get("station_id"),
                    "user_id": config.get("user_id"),
                    "request_id": f"auto-{str(uuid4())[:8]}",
                }

                sent = await self.send_personal_message(capture_request, connection_id)

                if sent:
                    self.connection_configs[connection_id]["last_capture"] = capture_request["timestamp"]
                    logger.info(f"Solicitação de captura enviada para {connection_id}")
                interval_seconds = config.get("interval_minutes", 5) * 60
                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.debug(f"Tarefa de monitoramento cancelada para {connection_id}")
        except Exception as e:
            logger.error(f"Erro no loop de monitoramento para {connection_id}: {e}")
            if connection_id in self.connection_configs:
                self.connection_configs[connection_id]["is_active"] = False


connection_manager = ConnectionManager()
