import logging
from typing import Dict

import asyncio
import aiohttp

from datetime import datetime

from .exceptions import NotFound, InvalidToken, Ratelimited, AmariServerError

from .objects import User, Leaderboard, Rewards

BASE_URL = "https://amaribot.com/api/v1/"

logger = logging.getLogger(__name__)

HTTP_response_errors = {
    404: NotFound,
    403: InvalidToken,
    429: Ratelimited,
    500: AmariServerError,
}


def check_response_for_errors(resp_status):
    if resp_status in HTTP_response_errors:
        raise HTTP_response_errors[resp_status]


class AmariBot:
    def __init__(self, token: str):

        if not isinstance(token, str):
            raise TypeError("The token must be a string.")

        self.baseurl = BASE_URL

        self.default_headers = {"Authorization": token}

        # Anti Ratelimit section
        self.requests = []

        self.max_requests = 30
        # Value in seconds
        self.request_period = 60

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

    async def get_user(self, guild_id: int, user_id: int) -> User:
        if not isinstance(guild_id, int):
            raise TypeError("The guild_id must be an int.")

        if not isinstance(user_id, int):
            raise TypeError("The user_id must be an int.")

        data = await self.create_request(
            "guild/{guild_id}/member/{user_id}".format(
                guild_id=guild_id, user_id=user_id
            ),
        )

        return User(data)

    async def get_leaderboard(
        self, guild_id: int, *, weekly: bool = False, page: int = 1, limit: int = 50
    ) -> Leaderboard:
        if not isinstance(guild_id, int):
            raise TypeError("The guild_id must be an int.")

        if not isinstance(weekly, bool):
            raise TypeError("The weekly variable must be a bool.")

        if not isinstance(page, int):
            raise TypeError("The page must be an int.")

        if not isinstance(limit, int):
            raise TypeError("The limit must be an int.")

        params = {"page": page, "limit": limit}

        data = await self.create_request(
            "guild/{lbtype}/{guild_id}".format(
                lbtype="weekly" if weekly else "leaderboard", guild_id=guild_id
            ),
            params=params,
        )

        data["id"] = guild_id
        return Leaderboard(data)

    async def get_rewards(
        self, guild_id: int, *, page: int = 1, limit: int = 50
    ) -> Rewards:
        if not isinstance(guild_id, int):
            raise TypeError("The guild_id must be an int.")

        if not isinstance(page, int):
            raise TypeError("The page must be an int.")

        if not isinstance(limit, int):
            raise TypeError("The limit must be an int.")

        params = {"page": page, "limit": limit}

        data = await self.create_request(
            "guild/rewards/{guild_id}".format(guild_id=guild_id),
            params=params,
        )

        data["id"] = guild_id
        return Rewards(data)

    async def create_request(self, endpoint: str, *, params: Dict = {}) -> Dict:
        await self.check_and_update_ratelimit()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.baseurl + endpoint,
                headers=self.default_headers,
                params=params,
            ) as response:

                check_response_for_errors(response.status)

                self.requests.append(datetime.utcnow())
                return await response.json()
