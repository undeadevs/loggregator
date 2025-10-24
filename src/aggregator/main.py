from datetime import datetime
import json
import os
from time import time
from typing import Annotated, List, Union
from fastapi import FastAPI, Query
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
import uvicorn
import dotenv

from aggregator import db, pubsub

start_time = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    global start_time
    dotenv.load_dotenv()
    asyncio.create_task(db.migrate())
    asyncio.create_task(pubsub.start())
    start_time = time()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/publish")
async def publish(event_or_events: Union[pubsub.Event, List[pubsub.Event]]):
    events = event_or_events if not(isinstance(event_or_events, pubsub.Event)) else [event_or_events]
    await pubsub.publish_events(events) 
    return {"message": "Success"}

class EventsQueryParams(BaseModel):
    topic: str

def event_dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: json.loads(value) if key=="payload" else value for key, value in zip(fields, row)}

@app.get("/events")
async def events(query: Annotated[EventsQueryParams, Query()]):
    events = []
    async with db.connect() as conn:
        conn.row_factory = event_dict_factory
        cursor = await conn.execute("SELECT * FROM events WHERE topic = ?", (query.topic,))
        events = await cursor.fetchall()
        await cursor.close()
    return {"events": events}

@app.get("/stats")
async def stats():
    uptime = time() - start_time
    duplicate_dropped = 0
    unique_processed = 0
    topics = []
    async with db.connect() as conn:
        cursor = await conn.execute("SELECT duplicate_dropped FROM stats WHERE id=1")
        stats_data = await cursor.fetchone()
        duplicate_dropped = 0 if stats_data is None else stats_data[0]
        await cursor.close()

        cursor = await conn.execute("SELECT COUNT(1) FROM events")
        events_count = await cursor.fetchone()
        unique_processed = 0 if events_count is None else events_count[0]
        await cursor.close()

        received = unique_processed + duplicate_dropped

        cursor = await conn.execute("SELECT DISTINCT topic FROM events ORDER BY timestamp ASC")
        topics_data = await cursor.fetchall()
        topics = [topic[0] for topic in topics_data]
        await cursor.close()

    return {"received": received, "unique_processed": unique_processed, "duplicate_dropped": duplicate_dropped, "topics": topics, "uptime": uptime*1000}

def run():
    uvicorn.run("aggregator.main:app", host=os.environ.get("HOST", "localhost"), port=int(os.environ.get("PORT", "8002")))

if __name__ == '__main__':
    run()
