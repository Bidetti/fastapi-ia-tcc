import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from src.modules.monitoring.usecase.monitoring_schedule_usecase import MonitoringScheduleUseCase
from src.modules.monitoring.usecase.monitoring_setup_usecase import MonitoringSetupUseCase
from src.shared.domain.models.http_models import (
    CaptureResultResponse,
    CaptureUpdateRequest,
    MonitoringSessionRequest,
    MonitoringSessionResponse,
    WebSocketConfigRequest,
)
from src.shared.infra.websocket.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

monitoring_router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


def get_monitoring_setup_usecase():
    return MonitoringSetupUseCase()


def get_monitoring_schedule_usecase():
    return MonitoringScheduleUseCase()


@monitoring_router.post("/sessions", response_model=MonitoringSessionResponse)
async def create_monitoring_session(
    request: MonitoringSessionRequest,
    monitoring_setup: MonitoringSetupUseCase = Depends(get_monitoring_setup_usecase),
):
    try:
        session = await monitoring_setup.create_session(
            station_id=request.station_id,
            user_id=request.user_id,
            interval_minutes=request.interval_minutes,
            metadata=request.metadata.model_dump() if request.metadata else None,
        )

        return MonitoringSessionResponse.model_validate(session.to_dict())

    except Exception as e:
        logger.exception(f"Erro ao criar sessão de monitoramento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de monitoramento: {str(e)}")


@monitoring_router.get("/sessions/{station_id}/{session_id}", response_model=MonitoringSessionResponse)
async def get_monitoring_session(
    station_id: str,
    session_id: str,
    monitoring_setup: MonitoringSetupUseCase = Depends(get_monitoring_setup_usecase),
):
    try:
        session = await monitoring_setup.get_session(station_id, session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Sessão de monitoramento não encontrada: {session_id}")

        return MonitoringSessionResponse.model_validate(session.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao recuperar sessão de monitoramento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar sessão: {str(e)}")


@monitoring_router.get("/sessions/active/{station_id}", response_model=Optional[MonitoringSessionResponse])
async def get_active_session(
    station_id: str,
    monitoring_setup: MonitoringSetupUseCase = Depends(get_monitoring_setup_usecase),
):
    try:
        session = await monitoring_setup.get_active_session(station_id)

        if not session:
            return None

        return MonitoringSessionResponse.model_validate(session.to_dict())

    except Exception as e:
        logger.exception(f"Erro ao recuperar sessão ativa para estação {station_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao recuperar sessão ativa para estação {station_id}: {str(e)}"
        )


@monitoring_router.put("/sessions/{station_id}/{session_id}", response_model=MonitoringSessionResponse)
async def update_monitoring_session(
    station_id: str,
    session_id: str,
    request: MonitoringSessionRequest,
    monitoring_setup: MonitoringSetupUseCase = Depends(get_monitoring_setup_usecase),
):
    try:
        session = await monitoring_setup.update_session(
            session_id=session_id,
            station_id=station_id,
            interval_minutes=request.interval_minutes,
            active=request.active,
            metadata=request.metadata.model_dump() if request.metadata else None,
        )

        if not session:
            raise HTTPException(status_code=404, detail=f"Sessão de monitoramento não encontrada: {session_id}")

        return MonitoringSessionResponse.model_validate(session.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao atualizar sessão de monitoramento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar sessão: {str(e)}")


@monitoring_router.post("/sessions/{station_id}/{session_id}/stop", response_model=Dict[str, bool])
async def stop_monitoring_session(
    station_id: str,
    session_id: str,
    monitoring_setup: MonitoringSetupUseCase = Depends(get_monitoring_setup_usecase),
):
    try:
        success = await monitoring_setup.stop_session(station_id, session_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Sessão de monitoramento não encontrada ou já encerrada: {session_id}"
            )

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao encerrar sessão de monitoramento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao encerrar sessão: {str(e)}")


@monitoring_router.post("/captures/{station_id}/{session_id}", response_model=CaptureResultResponse)
async def record_capture(
    station_id: str,
    session_id: str,
    request: CaptureUpdateRequest,
    monitoring_schedule: MonitoringScheduleUseCase = Depends(get_monitoring_schedule_usecase),
):
    try:
        capture_result = await monitoring_schedule.record_capture(
            station_id=station_id,
            session_id=session_id,
            image_id=request.image_id,
            image_url=str(request.image_url),
            metadata=request.metadata.model_dump() if request.metadata else None,
        )

        return CaptureResultResponse.model_validate(capture_result.to_dict())

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Erro ao registrar captura: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao registrar captura: {str(e)}")


@monitoring_router.put("/captures/{session_id}/{capture_id}", response_model=CaptureResultResponse)
async def update_capture(
    session_id: str,
    capture_id: str,
    request: CaptureUpdateRequest,
    monitoring_schedule: MonitoringScheduleUseCase = Depends(get_monitoring_schedule_usecase),
):
    try:
        capture_result = await monitoring_schedule.update_capture_status(
            session_id=session_id,
            capture_id=capture_id,
            status=request.status,
            result_ids=request.result_ids,
            metadata=request.metadata.model_dump() if request.metadata else None,
        )

        if not capture_result:
            raise HTTPException(status_code=404, detail=f"Captura não encontrada: {capture_id}")

        return CaptureResultResponse.model_validate(capture_result.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao atualizar captura: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar captura: {str(e)}")


@monitoring_router.get("/captures/{session_id}", response_model=List[CaptureResultResponse])
async def get_session_captures(
    session_id: str,
    monitoring_schedule: MonitoringScheduleUseCase = Depends(get_monitoring_schedule_usecase),
):
    try:
        captures = await monitoring_schedule.get_session_captures(session_id)

        return [CaptureResultResponse.model_validate(capture.to_dict()) for capture in captures]

    except Exception as e:
        logger.exception(f"Erro ao recuperar capturas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar capturas: {str(e)}")


@monitoring_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await connection_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "config":
                config = WebSocketConfigRequest.model_validate(data)

                monitoring_schedule = MonitoringScheduleUseCase()
                success = await monitoring_schedule.configure_websocket(
                    connection_id=connection_id,
                    station_id=config.station_id,
                    user_id=config.user_id,
                    interval_minutes=config.interval_minutes,
                )

                await websocket.send_json(
                    {"type": "config_response", "success": success, "connection_id": connection_id}
                )

            elif message_type == "capture_response":
                image_id = data.get("image_id")
                image_url = data.get("image_url")
                request_id = data.get("request_id")
                station_id = data.get("station_id")

                monitoring_setup = MonitoringSetupUseCase()
                session = await monitoring_setup.get_active_session(station_id)

                if session and image_id and image_url:
                    monitoring_schedule = MonitoringScheduleUseCase()
                    await monitoring_schedule.record_capture(
                        station_id=station_id,
                        session_id=session.session_id,
                        image_id=image_id,
                        image_url=image_url,
                        metadata={
                            "request_id": request_id,
                            "automatic": True,
                            "source": "websocket",
                            "connection_id": connection_id,
                        },
                    )

                    await websocket.send_json({"type": "capture_recorded", "success": True, "request_id": request_id})
                else:
                    await websocket.send_json(
                        {
                            "type": "capture_recorded",
                            "success": False,
                            "request_id": request_id,
                            "error": "Sessão ativa não encontrada ou dados incompletos",
                        }
                    )

            elif message_type == "start_monitoring":
                monitoring_schedule = MonitoringScheduleUseCase()
                success = await monitoring_schedule.start_monitoring(connection_id)

                await websocket.send_json(
                    {
                        "type": "monitoring_status",
                        "status": "started" if success else "error",
                        "connection_id": connection_id,
                    }
                )

            elif message_type == "stop_monitoring":
                monitoring_schedule = MonitoringScheduleUseCase()
                success = await monitoring_schedule.stop_monitoring(connection_id)

                await websocket.send_json(
                    {
                        "type": "monitoring_status",
                        "status": "stopped" if success else "error",
                        "connection_id": connection_id,
                    }
                )

            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Tipo de mensagem desconhecido: {message_type}"}
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(connection_id)
    except Exception as e:
        logger.exception(f"Erro no WebSocket {connection_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": f"Erro interno: {str(e)}"})
        except Exception:
            pass
        connection_manager.disconnect(connection_id)
