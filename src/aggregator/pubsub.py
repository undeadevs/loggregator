import asyncio
from datetime import datetime
import json
from typing import List
from uuid import UUID
from aggregator import db
from common.event import Event
from pydantic import BaseModel

queue = None

async def start():
    global queue
    queue = asyncio.Queue()
    while True:
        event = await queue.get()
        async with db.connect() as conn:
            cursor = await conn.execute("SELECT topic, event_id FROM events WHERE topic=? AND event_id=?", (event.topic, str(event.event_id)))
            existing_event = await cursor.fetchone()
            await cursor.close()
            if existing_event is not None:
                print(f"Duplicate {(event.topic, event.event_id)}")
                await conn.execute("""
                    INSERT INTO 
                    stats(id,duplicate_dropped) 
                    VALUES(
                        1,
                        1
                    ) ON CONFLICT(id) DO UPDATE SET duplicate_dropped=duplicate_dropped+1
                    """)
                await conn.commit()
                continue
            await conn.execute("INSERT INTO events VALUES(?,?,?,?,?) ON CONFLICT DO NOTHING", (event.topic, str(event.event_id), event.timestamp, event.source, json.dumps(event.payload)))
            await conn.commit()
        asyncio.create_task(consume_event(event))


async def consume_event(event: Event):
    print(event)
    pass


async def publish_event(event: Event):
    global queue
    if queue is None:
        raise Exception("Not started")
    await queue.put(event)

async def publish_events(events: List[Event]):
    await asyncio.gather(*[publish_event(event) for event in events])
