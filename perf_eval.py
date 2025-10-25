from functools import reduce
import aiohttp
import asyncio
import os
from src.common.publishing import generate_events, publish_events_batched, publish_events_single
import dotenv
from time import time

dotenv.load_dotenv()

url = f"http://{os.environ.get("AGGREGATOR_HOST", "localhost")}:{os.environ.get("AGGREGATOR_PORT", "8002")}/publish"

event_counts = [50, 100, 500, 1000, 5000, 10000]

async def main():
    single_perfs = []
    batched_perfs = []
    min_dup_rate = 0.2
    max_dup_rate = 1.0
    async with aiohttp.ClientSession() as session:
        for event_count in event_counts:
            start = time()
            await publish_events_single(session, url, generate_events(event_count, min_dup_rate, max_dup_rate))
            end = time()
            elapsed = end - start
            single_perfs.append(elapsed)
        for event_count in event_counts:
            start = time()
            await publish_events_batched(session, url, generate_events(event_count, min_dup_rate, max_dup_rate))
            end = time()
            elapsed = end - start
            batched_perfs.append(elapsed)

    print("")
    print(f"Cases: {",".join([str(c) for c in event_counts])}")
    print(f"{min_dup_rate * 100:.2f}% <= Duplicate Rate <= {max_dup_rate * 100:.2f}% ")
    print("")

    print("Single")
    for event_count, perf in zip(event_counts, single_perfs):
        print(f"{event_count}: {perf:.10f}s, T={event_count // perf} event/s, L={perf / event_count:.10f} s/event")
    print(f"AVG T={reduce(lambda acc,curr: acc + (curr[0] // curr[1]), list(zip(event_counts, single_perfs)),0) // len(event_counts)} event/s")
    print(f"AVG L={reduce(lambda acc,curr: acc + (curr[1] / curr[0]), list(zip(event_counts, single_perfs)),0) / len(event_counts):.10f} s/event")

    print("")

    print("Batched")
    for event_count, perf in zip(event_counts, batched_perfs):
        print(f"{event_count}: {perf:.10f}s, T={event_count // perf} event/s, L={perf / event_count:.10f} s/event")
    print(f"AVG T={reduce(lambda acc,curr: acc + (curr[0] // curr[1]), list(zip(event_counts, batched_perfs)),0) // len(event_counts)} event/s")
    print(f"AVG L={reduce(lambda acc,curr: acc + (curr[1] / curr[0]), list(zip(event_counts, batched_perfs)),0) / len(event_counts):.10f} s/event")


if __name__ == '__main__':
    asyncio.run(main())
