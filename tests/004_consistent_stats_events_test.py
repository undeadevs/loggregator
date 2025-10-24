import asyncio
import logging
import subprocess
from time import sleep
import aiohttp
import pytest
import sys
import os
from uuid import uuid4
from common.publishing import publish_events_single
from common.event import Event
import datetime

endpoint = f"http://{os.environ.get("HOST", "localhost")}:{os.environ.get("PORT", "8002")}"

logger = logging.getLogger(__name__)

env = os.environ.copy()
env["DB_PATH"] = f"./{os.path.basename(__file__).removesuffix('.py')}.db"

@pytest.fixture()
def server():
    global env
    process = subprocess.Popen([sys.executable, './src/aggregator/main.py'], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    sleep(2.0)

    yield process
    sleep(2.0)
    process.terminate()
    process.wait()
    os.remove(env["DB_PATH"])

@pytest.mark.asyncio
async def test_consistent_stats_events(server):
    async with aiohttp.ClientSession() as session:
        events = [
            Event(
                topic = "foo", 
                event_id = uuid4(), 
                timestamp = datetime.datetime.now(), 
                source = "somewhere",
                payload = {
                    "data": "bar",
                },
            ),
            Event(
                topic = "bar", 
                event_id = uuid4(), 
                timestamp = datetime.datetime.now(), 
                source = "somewhere",
                payload = {
                    "data": "bar",
                },
            ),
            Event(
                topic = "baz", 
                event_id = uuid4(), 
                timestamp = datetime.datetime.now(), 
                source = "somewhere",
                payload = {
                    "data": "bar",
                },
            ),
        ]
        events.extend([
            Event(
                topic = "foo", 
                event_id = events[0].event_id, 
                timestamp = datetime.datetime.now(), 
                source = "somewhere",
                payload = {
                    "data": "bar",
                },
            ),
            Event(
                topic = "bar", 
                event_id = events[1].event_id, 
                timestamp = datetime.datetime.now(), 
                source = "somewhere",
                payload = {
                    "data": "bar",
                },
            ),
        ])
        await publish_events_single(session, f"{endpoint}/publish", events)
        await asyncio.sleep(2.0)
        res = await session.get(f"{endpoint}/stats")
        res_data = await res.json()
        assert (
            res_data["received"], 
            res_data["unique_processed"], 
            res_data["duplicate_dropped"], 
            res_data["topics"]
        ) == (
            5, 
            3, 
            2, 
            ["foo", "bar", "baz"]
        )
