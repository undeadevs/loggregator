import asyncio
from time import time
import aiohttp
from random import randint
import os
from common.publishing import generate_events, publish_events_sparsed
import dotenv

dotenv.load_dotenv()

url = f"http://{os.environ.get("AGGREGATOR_HOST", "localhost")}:{os.environ.get("AGGREGATOR_PORT", "8002")}/publish"

async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            events = generate_events(5000, 0.2)
            start = time()
            await publish_events_sparsed(session, url, events)
            end = time()
            print(f"Completed in {end - start}")
            await asyncio.sleep(randint(15,30))

if __name__ == '__main__':
    asyncio.run(main())
