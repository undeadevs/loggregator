import logging
import subprocess
from time import sleep
import aiohttp
import pytest
import sys
import os
from uuid import uuid4
from common.publishing import publish
from common.event import Event
import datetime

endpoint = f"http://{os.environ.get("HOST", "localhost")}:{os.environ.get("PORT", "8002")}"

logger = logging.getLogger(__name__)

env = os.environ.copy()
env["DB_PATH"] = f"./{os.path.basename(__file__).removesuffix('.py')}.db"

@pytest.fixture()
def server():
    global env
    process = subprocess.Popen([sys.executable, './src/aggregator/main.py'], env=env, text=True)
    sleep(2.0)
    yield
    sleep(2.0)
    process.terminate()
    process.wait()
    os.remove(env["DB_PATH"])

@pytest.mark.asyncio
async def test_dedup_validation(server):
    async with aiohttp.ClientSession() as session:
        event = Event(
            topic = "foo", 
            event_id = uuid4(), 
            timestamp = datetime.datetime.now(), 
            source = "somewhere",
            payload = {
                "data": "bar",
            },
        )
        await publish(session, f"{endpoint}/publish", event)
        event.timestamp = datetime.datetime.now()
        await publish(session, f"{endpoint}/publish", event)
        res = await session.get(f"{endpoint}/stats")
        res_data = await res.json()
        assert res_data["unique_processed"] == 1
