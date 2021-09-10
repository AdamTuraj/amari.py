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
    """
    The client used to make requests to the Amari API.

    Attributes
    ----------
    session: aiohttp.ClientSession
        The client session used to make requests to the Amari API.
    """

    BASE_URL = "https://amaribot.com/api/v1/"

    HTTP_response_errors = {
        404: NotFound,
        403: InvalidToken,
        429: RatelimitException,
        500: AmariServerError,
    }

    def __init__(self, token: str, /, *, session: Optional[aiohttp.ClientSession] = None):
        self.session = session or aiohttp.ClientSession()
        self._default_headers = {"Authorization": token}

        # Anti Ratelimit section
        self.requests = []
        self.max_requests = 60
        self.request_period = 60

    async def close(self):
        """
        Closes the client resources.

        This must be called once the client is no longer in use.
        """
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
        for count in range(1, 6):
            wait_amount = 2 ** count

            logger.warning(
                "Slow down, you are about to be rate limited."
                f"Trying again in {wait_amount} seconds."
            )
            await asyncio.sleep(wait_amount)

            self.update_ratelimit()
            if len(self.requests) != self.max_requests - 1:
                break

    async def fetch_user(self, guild_id: int, user_id: int) -> User:
        """
        Fetches a user from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the user from.
        user_id: int
            The user's ID.
        """
        data = await self.request(f"guild/{guild_id}/member/{user_id}")
        return User(guild_id, data)

    async def fetch_leaderboard(
        self,
        guild_id: int,
        /,
        *,
        weekly: bool = False,
        raw: bool = False,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Leaderboard:
        """
        Fetches a guild's leaderboard from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the leaderboard from.
        weekly: bool
            Choose either to fetch the weekly leaderboard or the regular leaderboard.
        raw: bool
            Whether or not to use the raw endpoint. Raw endpoints do not support pagination but
            will return the entire leaderboard.
        page: int
            The leaderboard page to fetch.
        limit: int
            The amount of users to fetch per page.

        Returns
        -------
        Leaderboard
            The guild's leaderboard.
        """
        params = {}
        if raw and page:
            raise ValueError("raw endpoints do not support pagination")
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        lb_type = "weekly" if weekly else "leaderboard"
        endpoint = ["guild", lb_type, str(guild_id)]
        if raw:
            endpoint.insert(1, "raw")
        data = await self.request("/".join(endpoint), params=params)
        return Leaderboard(guild_id, data)

    async def fetch_full_leaderboard(
        self, guild_id: int, /, *, weekly: bool = False
    ) -> Leaderboard:
        """
        Fetches a guild's full leaderboard from the Amari API.

        This uses pagination to make fetch a full leaderboard by making multiple requests.
        Consider using the raw endpoints to fetch the full leaderboard without making multiple requests.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the leaderboard from.
        weekly: bool
            Choose either to fetch the weekly leaderboard or the regular leaderboard.

        Returns
        -------
        Leaderboard
            The guild's leaderboard.
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

    async def fetch_rewards(self, guild_id: int, /, *, page: int = 1, limit: int = 50) -> Rewards:
        """
        Fetches a guild's role rewards from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the role rewards from.
        page: int
            The rewards page to fetch.
        limit: int
            The amount of rewards to fetch per page.

        Returns
        -------
        Rewards
            The guild's role rewards.
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
            except Exception:  # skipcq PYL-W0703
                message = await response.text()
            raise error(response, message)

    async def request(self, endpoint: str, *, params: Dict = {}) -> Dict:
        await self.check_and_update_ratelimit()
        async with self.session.get(
            url=self.BASE_URL + endpoint,
            headers=self._default_headers,
            params=params,
        ) as response:
            await self.check_response_for_errors(response)
            self.requests.append(datetime.utcnow())
            return await response.json()
