import logging
from typing import Dict, Optional

import asyncio
import aiohttp

from datetime import datetime

from .exceptions import HTTPException, NotFound, InvalidToken, Ratelimited, AmariServerError
from .objects import User, Leaderboard, Rewards

__all__ = ("AmariClient",)

logger = logging.getLogger(__name__)


class AmariClient:
    BASE_URL = "https://amaribot.com/api/v1/"

    HTTP_response_errors = {
        404: NotFound,
        403: InvalidToken,
        429: Ratelimited,
        500: AmariServerError,
    }

    def __init__(self, token: str, *, session: Optional[aiohttp.ClientSession] = None):
        self.session = session or aiohttp.ClientSession()
        self.default_headers = {"Authorization": token}

        # Anti Ratelimit section
        self.requests = []
        self.max_requests = 60
        self.request_period = 60

    async def close(self):
        await self.session.close()

    def update_ratelimit(self):
        for request_time in self.requests:
            if (datetime.utcnow() - request_time).seconds >= self.request_period:
                self.requests.remove(request_time)

    async def check_and_update_ratelimit(self):
        self.update_ratelimit()

        if len(self.requests) == self.max_requests - 1:
            await self.wait_for_ratelimit_end()

    async def wait_for_ratelimit_end(self):
        test = 0
        for count in range(1, 6):
            wait_amount = 2 ** count
            test += wait_amount

            logger.warning(
                f"Slow down, you are about to be rate limited. Trying again in {wait_amount} seconds."
            )
            await asyncio.sleep(wait_amount)

            self.update_ratelimit()
            if len(self.requests) != self.max_requests - 1:
                break

    async def fetch_user(self, guild_id: int, user_id: int) -> User:
        data = await self.request(f"guild/{guild_id}/member/{user_id}")
        return User(data)

    async def fetch_leaderboard(
        self, guild_id: int, *, weekly: bool = False, page: int = 1, limit: int = 50
    ) -> Leaderboard:
        params = {"page": page, "limit": limit}
        lb_type = "weekly" if weekly else "leaderboard"
        data = await self.request(f"guild/{lb_type}/{guild_id}", params=params)
        data["id"] = guild_id
        return Leaderboard(data)

    async def fetch_rewards(
        self, guild_id: int, *, page: int = 1, limit: int = 50
    ) -> Rewards:
        params = {"page": page, "limit": limit}
        data = await self.request(f"guild/rewards/{guild_id}", params=params)
        data["id"] = guild_id
        return Rewards(data)

    @classmethod
    async def check_response_for_errors(cls, response: aiohttp.ClientResponse):
        if response.status > 399 or response.status < 200:
            error = cls.HTTP_response_errors.get(response.status, HTTPException)
            try:
                message = (await response.json())["error"] # clean this up later
            except Exception:
                message = await response.text()
            raise error(response, message)

    async def request(self, endpoint: str, *, params: Dict = {}) -> Dict:
        await self.check_and_update_ratelimit()
        async with self.session.get(
            url=self.BASE_URL + endpoint,
            headers=self.default_headers,
            params=params,
        ) as response:
            self.check_response_for_errors(response)
            self.requests.append(datetime.utcnow())
            return await response.json()
