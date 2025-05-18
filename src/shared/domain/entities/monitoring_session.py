from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class CaptureResult:
    def __init__(
        self,
        image_id: str,
        capture_id: Optional[str] = None,
        image_url: Optional[str] = None,
        result_ids: Optional[List[str]] = None,
        status: str = "pending",
        capture_timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.capture_id = capture_id or f"cap-{uuid4()}"
        self.image_id = image_id
        self.image_url = image_url
        self.result_ids = result_ids or []
        self.status = status
        self.capture_timestamp = capture_timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capture_id": self.capture_id,
            "image_id": self.image_id,
            "image_url": self.image_url,
            "result_ids": self.result_ids,
            "status": self.status,
            "capture_timestamp": self.capture_timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaptureResult":
        capture_timestamp = None
        if data.get("capture_timestamp"):
            try:
                capture_timestamp = datetime.fromisoformat(data["capture_timestamp"])
            except ValueError:
                capture_timestamp = datetime.now(timezone.utc)

        return cls(
            capture_id=data.get("capture_id"),
            image_id=data["image_id"],
            image_url=data.get("image_url"),
            result_ids=data.get("result_ids", []),
            status=data.get("status", "pending"),
            capture_timestamp=capture_timestamp,
            metadata=data.get("metadata", {}),
        )


class MonitoringSession:
    def __init__(
        self,
        station_id: str,
        user_id: str,
        interval_minutes: int = 5,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        active: bool = True,
        captures: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.session_id = session_id or f"sess-{uuid4()}"
        self.station_id = station_id
        self.user_id = user_id
        self.interval_minutes = interval_minutes
        self.start_time = start_time or datetime.now(timezone.utc)
        self.end_time = end_time
        self.active = active
        self.captures = captures or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "station_id": self.station_id,
            "user_id": self.user_id,
            "interval_minutes": self.interval_minutes,
            "start_time": self.start_time.isoformat(),
            "active": self.active,
            "captures": self.captures,
            "metadata": self.metadata,
        }

        if self.end_time:
            result["end_time"] = self.end_time.isoformat()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitoringSession":
        start_time = None
        if data.get("start_time"):
            try:
                start_time = datetime.fromisoformat(data["start_time"])
            except ValueError:
                start_time = datetime.now(timezone.utc)

        end_time = None
        if data.get("end_time"):
            try:
                end_time = datetime.fromisoformat(data["end_time"])
            except ValueError:
                end_time = None

        return cls(
            session_id=data.get("session_id"),
            station_id=data["station_id"],
            user_id=data["user_id"],
            interval_minutes=data.get("interval_minutes", 5),
            start_time=start_time,
            end_time=end_time,
            active=data.get("active", True),
            captures=data.get("captures", []),
            metadata=data.get("metadata", {}),
        )
