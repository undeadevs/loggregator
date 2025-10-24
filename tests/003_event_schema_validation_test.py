import logging
from uuid import uuid4
from common.event import Event
import datetime

from pydantic import ValidationError

logger = logging.getLogger(__name__)

def test_event_schema_validation_valid():
    errors = []
    data = {
        "topic": "foo",
        "event_id": uuid4(),
        "timestamp": datetime.datetime.now(),
        "source": "somewhere",
        "payload": {},
    }
    try:
        Event(**data)
    except ValidationError as e:
        errors = e.errors()
    assert len(errors) == 0

def test_event_schema_validation_missing():
    errors = []
    data = {
        "event_id": uuid4(),
        "timestamp": datetime.datetime.now(),
        "source": "somewhere",
        "payload": {},
    }
    try:
        Event(**data)
    except ValidationError as e:
        errors = e.errors()
    assert errors[0] == {
        "type": "missing", 
        "loc": ("topic",), 
        "msg": "Field required", 
        "input": data, 
        "url": errors[0].get("url")
    }

def test_event_schema_validation_invalid_topic():
    errors = []
    data = {
        "topic": 100,
        "event_id": uuid4(),
        "timestamp": datetime.datetime.now(),
        "source": "somewhere",
        "payload": {},
    }
    try:
        Event(**data)
    except ValidationError as e:
        errors = e.errors()
    assert errors[0] == {
        "type": "string_type", 
        "loc": ("topic",), 
        "msg": "Input should be a valid string", 
        "input": data["topic"], 
        "url": errors[0].get("url")
    }

def test_event_schema_validation_invalid_event_id():
    errors = []
    data = {
        "topic": "foo",
        "event_id": "1",
        "timestamp": datetime.datetime.now(),
        "source": "somewhere",
        "payload": {},
    }
    try:
        Event(**data)
    except ValidationError as e:
        errors = e.errors()
    assert errors[0] == {
        "type": "uuid_parsing", 
        "loc": ("event_id",), 
        "msg": f"Input should be a valid UUID, invalid length: expected length 32 for simple format, found {len(data["event_id"])}", 
        "input": data["event_id"], 
        "ctx": {
            "error": f"invalid length: expected length 32 for simple format, found {len(data["event_id"])}",
        },
        "url": errors[0].get("url")
    }

def test_event_schema_validation_invalid_timestamp():
    errors = []
    data = {
        "topic": "foo",
        "event_id": uuid4(),
        "timestamp": "hello",
        "source": "somewhere",
        "payload": {},
    }
    try:
        Event(**data)
    except ValidationError as e:
        errors = e.errors()
    assert errors[0] == {
        "type": "datetime_from_date_parsing", 
        "loc": ("timestamp",), 
        "msg": "Input should be a valid datetime or date, input is too short", 
        "input": data["timestamp"], 
        "ctx": {
            "error": "input is too short",
        },
        "url": errors[0].get("url")
    }
