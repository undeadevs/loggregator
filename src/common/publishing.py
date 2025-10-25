import datetime
from typing import List, Union
import uuid
import aiohttp
from random import choice, randint, uniform
from string import ascii_letters
from common.event import Event
from math import floor

def randstr(min, max):
    return ''.join(choice(ascii_letters) for i in range(randint(min,max)))

def randtopic():
    return ''.join([randstr(5,10) for _ in range(randint(1,5))])

async def publish(session: aiohttp.ClientSession, url, event_or_events: Union[Event, List[Event]]):
    event_or_events_dict = event_or_events.model_dump(mode='json') if isinstance(event_or_events, Event) else [event.model_dump(mode='json') for event in event_or_events]
    async with session.post(url, json=event_or_events_dict) as res:
        print(await res.json())

def generate_events(n=1, min_dup_split=0.0, max_dup_split=0.0, *, topic: str|None = None, event_id: uuid.UUID|None = None, timestamp: datetime.datetime|None = None, source: str|None = None, payload: dict|None = None):
    dup_split = uniform(min_dup_split, max_dup_split)
    dup_n = floor(n*dup_split)
    unq_n = n-dup_n
    events = []
    for i in range(n):
        is_dup = uniform(0,1) > (1 / ((i+1) / 2))
        if is_dup and dup_n > 0 and len(events) > 0:
            dup_n -= 1
            event = choice(events)
            event.timestamp = datetime.datetime.now()
            events.append(event)
        else:
            unq_n -= 1
            events.append(Event(
                topic=randtopic() if topic is None else topic, 
                event_id=uuid.uuid4() if event_id is None else event_id, 
                timestamp=datetime.datetime.now() if timestamp is None else timestamp, 
                source=randstr(5,10) if source is None else source,
                payload={
                    "data": randstr(100,1000),
                } if payload is None else payload,
            ))
    return events

async def publish_events_single(session: aiohttp.ClientSession, url, events: List[Event]):
    for event in events:
        await publish(session, url, event)

async def publish_events_batched(session: aiohttp.ClientSession, url, events: List[Event]):
    await publish(session, url, events)

async def publish_events_sparsed(session: aiohttp.ClientSession, url, events: List[Event]):
    events_copied = events.copy()
    events_n = len(events_copied)
    while events_n > 0:
        batched = randint(0,1)
        if batched==1:
            batch_size = randint(1,events_n)
            await publish(session, url, events_copied[0:batch_size])
            events_copied = events_copied[batch_size:]
            events_n -= batch_size
        else:
            await publish(session, url, events_copied[0])
            events_copied.pop(0)
            events_n -= 1
