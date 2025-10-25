from datetime import datetime
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, StringConstraints


class Event(BaseModel):
    topic: Annotated[str, StringConstraints(pattern=r"^([a-z_A-Z0-9]+\.){0,4}[a-z_A-Z0-9]+$")]
    event_id: UUID
    timestamp: datetime
    source: str
    payload: dict
