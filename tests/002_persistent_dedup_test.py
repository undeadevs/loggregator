import logging
import subprocess
from time import sleep
import aiohttp
import pytest
import sys
import os
import asyncio
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
    process = subprocess.Popen([sys.executable, './src/aggregator/main.py'], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    sleep(2.0)

    def _get_process():
        return process

    def _set_process(new_process):
        nonlocal process
        process = new_process

    yield {"get": _get_process, "set": _set_process}
    sleep(2.0)
    process.terminate()
    process.wait()
    os.remove(env["DB_PATH"])

@pytest.mark.asyncio
async def test_persistent_dedup(server):
    global env
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
        process = server["get"]()
        # terminate server process - simulating crashes
        process.terminate()
        process.wait()
        # rerun server process
        process = subprocess.Popen([sys.executable, './src/aggregator/main.py'], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        await asyncio.sleep(2.0)
        server["set"](process)
    async with aiohttp.ClientSession() as session:
        event.timestamp = datetime.datetime.now()
        await publish(session, f"{endpoint}/publish", event)
        res = await session.get(f"{endpoint}/stats")
        res_data = await res.json()
        assert res_data["unique_processed"] == 1
