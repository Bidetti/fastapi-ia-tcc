from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class MonitoringMetadata(BaseModel):
    device_info: Optional[str] = None
    location: Optional[str] = None
    fruit_type: Optional[str] = None
    notes: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class MonitoringSessionRequest(BaseModel):
    station_id: str
    user_id: str
    interval_minutes: int = Field(5, ge=1, le=60)
    active: Optional[bool] = True
    metadata: Optional[MonitoringMetadata] = None


class MonitoringSessionResponse(BaseModel):
    session_id: str
    station_id: str
    user_id: str
    interval_minutes: int
    active: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    captures: List[str] = []
    metadata: Dict[str, Any] = {}


class CaptureUpdateRequest(BaseModel):
    image_id: str
    image_url: HttpUrl
    status: str = "captured"
    result_ids: Optional[List[str]] = None
    metadata: Optional[MonitoringMetadata] = None


class CaptureResultResponse(BaseModel):
    capture_id: str
    image_id: str
    image_url: Optional[HttpUrl] = None
    result_ids: List[str] = []
    status: str
    capture_timestamp: datetime
    metadata: Dict[str, Any] = {}


class WebSocketConfigRequest(BaseModel):
    type: str = "config"
    station_id: str
    user_id: str
    interval_minutes: int = Field(5, ge=1, le=60)
