from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class Event(BaseModel):
    topic: str
    event_id: UUID
    timestamp: datetime
    source: str
    payload: dict
