import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import math

import aiohttp

from .exceptions import (
    AmariServerError,
    HTTPException,
    InvalidToken,
    NotFound,
    RatelimitException,
)
from .objects import Leaderboard, Rewards, User

__all__ = ("AmariClient",)

logger = logging.getLogger(__name__)


class AmariClient:
    BASE_URL = "https://amaribot.com/api/v1/"

    HTTP_response_errors = {
        404: NotFound,
        403: InvalidToken,
        429: RatelimitException,
        500: AmariServerError,
    }

    def __init__(
        self, token: str, /, *, session: Optional[aiohttp.ClientSession] = None
    ):
        self.session = session or aiohttp.ClientSession()
        self.default_headers = {"Authorization": token}

        # Anti Ratelimit section
        self.requests = []
        self.max_requests = 60
        self.request_period = 60

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()

            if loop.is_running():
                loop.create_task(self.session.close())
            else:
                loop.run_until_complete(self.session.close())

        except Exception:
            pass

    def update_ratelimit(self):
        for request_time in self.requests:
            if (datetime.utcnow() - request_time).seconds >= self.request_period:
                self.requests.remove(request_time)

    async def check_and_update_ratelimit(self):
        self.update_ratelimit()

        if len(self.requests) == self.max_requests - 1:
            await self.wait_for_ratelimit_end()

    async def wait_for_ratelimit_end(self):
        for count in range(1, 6):
            wait_amount = 2 ** count

            logger.warning(
                f"Slow down, you are about to be rate limited. Trying again in {wait_amount} seconds."
            )
            await asyncio.sleep(wait_amount)

            self.update_ratelimit()
            if len(self.requests) != self.max_requests - 1:
                break

    async def fetch_user(self, guild_id: int, user_id: int) -> User:
        """Fetches a user

        Args:
            guild_id (int): The guild id of the guild you are getting the user from
            user_id (int): The user id of the user you are requesting

        Returns:
            User
        """
        data = await self.request(f"guild/{guild_id}/member/{user_id}")
        return User(guild_id, data)

    async def fetch_leaderboard(
        self, guild_id: int, /, *, weekly: bool = False, page: int = 1, limit: int = 50
    ) -> Leaderboard:
        """Fetches a guilds leaderboard

        Args:
            guild_id (int): The id of the guild you are fetching the leaderboard from
            weekly (bool, optional): Choose either to fetch the weekly leaderboard or the regular leaderboard. Defaults to False.
            page (int, optional): The leaderboard page you are fetching. Defaults to 1.
            limit (int, optional): The amount of users that will be on the requested page. Defaults to 50.

        Returns:
            Leaderboard
        """
        params = {"page": page, "limit": limit}
        lb_type = "weekly" if weekly else "leaderboard"
        data = await self.request(f"guild/{lb_type}/{guild_id}", params=params)
        return Leaderboard(guild_id, data)

    async def fetch_full_leaderboard(
        self, guild_id: int, /, *, weekly: bool = False
    ) -> Leaderboard:
        """Fetches the entire leaderboard of a guild

        Args:
            guild_id (int): The id of the guild you are fetching the leaderboard from
            weekly (bool, optional): Choose either to fetch the weekly leaderboard or the regular leaderboard. Defaults to False.

        Returns:
            Leaderboard
        """
        lb_type = "weekly" if weekly else "leaderboard"

        main_leaderboard = Leaderboard(
            guild_id,
            await self.request(f"guild/{lb_type}/{guild_id}", params={"limit": 1000}),
        )

        main_leaderboard.user_count = main_leaderboard.total_count

        required_requests = math.ceil(main_leaderboard.total_count / 1000) - 1

        for page in range(required_requests):
            request = await self.request(
                f"guild/{lb_type}/{guild_id}",
                params={"page": page + 2, "limit": 1000},
            )

            leaderboard = Leaderboard(guild_id, request)

            for user in leaderboard.users.values():
                main_leaderboard.add_user(user)

        return main_leaderboard

    async def fetch_rewards(
        self, guild_id: int, /, *, page: int = 1, limit: int = 50
    ) -> Rewards:
        """Fetches a guilds role rewards

        Args:
            guild_id (int): The guild id you are requesting the role rewards from
            page (int, optional): The reward page you are requesting. Defaults to 1.
            limit (int, optional): The amount of rewards that will be on the requested page. Defaults to 50.

        Returns:
            Rewards
        """
        params = {"page": page, "limit": limit}
        data = await self.request(f"guild/rewards/{guild_id}", params=params)
        return Rewards(guild_id, data)

    @classmethod
    async def check_response_for_errors(cls, response: aiohttp.ClientResponse):
        if response.status > 399 or response.status < 200:
            error = cls.HTTP_response_errors.get(response.status, HTTPException)
            try:
                message = (await response.json())["error"]  # clean this up later
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
            await self.check_response_for_errors(response)
            self.requests.append(datetime.utcnow())
            return await response.json()
