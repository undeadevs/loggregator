import logging
import subprocess
from time import sleep, time
import aiohttp
import pytest
import sys
import os
from common.publishing import generate_events, publish_events_batched

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
    def wait_until_terminate():
        try:
            process.terminate()
            process.wait(2.0)
        except subprocess.TimeoutExpired:
            wait_until_terminate()
    wait_until_terminate()
    os.remove(env["DB_PATH"])

@pytest.mark.asyncio
async def test_batch_events_time_10(server):
    async with aiohttp.ClientSession() as session:
        events = generate_events(10, 0.0, 0.0)
        start_time = time()
        await publish_events_batched(session, f"{endpoint}/publish", events)
        elapsed_time = time() - start_time
        assert elapsed_time <= 0.5

@pytest.mark.asyncio
async def test_batch_events_time_100(server):
    async with aiohttp.ClientSession() as session:
        events = generate_events(100, 0.0, 0.0)
        start_time = time()
        await publish_events_batched(session, f"{endpoint}/publish", events)
        elapsed_time = time() - start_time
        assert elapsed_time <= 0.5
