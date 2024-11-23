import asyncio
import time
from typing import Any, Awaitable, Callable, Tuple

from amari import AmariClient


async def time_it(func: Callable[[], Awaitable[Any]]) -> Tuple[Any, float]:
    s = time.perf_counter()
    ret = await func
    e = time.perf_counter()
    return ret, round(((e - s) * 1000), 4)


async def main():
    async with AmariClient(
        "TOKEN",  # your Amari API token here
        max_requests=5,
        maxbytes=32 * 1024,  # this is in bytes
        cache_ttl=60,  # ttl is in seconds
    ) as client:
        # initial request, so user is not in cache
        users, time_taken = await time_it(
            client.fetch_users(941056850386890842, [613752401878450176], cache=True)
        )
        print(1, users, time_taken)  # result: 316.5056 ms

        users, time_taken = await time_it(
            client.fetch_users(941056850386890842, [613752401878450176], cache=True)
        )
        print(2, users, time_taken)  # result: 0.0163 ms

        # now use the fetch_user function instead
        user, time_taken = await time_it(
            client.fetch_user(941056850386890842, 613752401878450176, cache=True)
        )
        print(3, user, time_taken)  # result: 0.0169 ms

        # now we will add a uncached user to the request
        users, time_taken = await time_it(
            client.fetch_users(
                941056850386890842, [613752401878450176, 921020428791742515], cache=True
            )
        )
        print(4, users, time_taken)  # result: 119.3746 ms

        users, time_taken = await time_it(
            client.fetch_users(
                941056850386890842, [613752401878450176, 921020428791742515], cache=True
            )
        )
        print(5, users, time_taken)  # result: 0.0357

        # now let's do the same request but not use cache
        users, time_taken = await time_it(
            client.fetch_users(
                941056850386890842,
                [613752401878450176, 921020428791742515],
                cache=False,
            )
        )
        print(6, users, time_taken)  # result: 134.3325 ms


if __name__ == "__main__":
    asyncio.run(main())
