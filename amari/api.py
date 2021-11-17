import asyncio
import logging
import time
from typing import Dict, List, Optional

import aiohttp

from .exceptions import (
    AmariServerError,
    HTTPException,
    InvalidToken,
    NotFound,
    RatelimitException,
)
from .objects import Leaderboard, Rewards, User, Users

__all__ = ("AmariClient",)

logger = logging.getLogger(__name__)


class AmariClient:
    """
    The client used to make requests to the Amari API.

    Attributes
    ----------
    useAntiRatelimit: bool
        Whether to use the anti ratelimit or not.
        IT IS VERY UNRECOMMENDED TO DISABLE THIS FEATURE
        AS IT CAN LEAD TO RATELIMITS

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

    def __init__(
        self,
        token: str,
        /,
        *,
        useantiratelimit: bool = True,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        self.session = session or aiohttp.ClientSession()
        self._default_headers = {"Authorization": token}

        self.lock = asyncio.Lock()

        # Anti Ratelimit section
        self.useantiratelimit = useantiratelimit

        self.requests = 0
        self.last_reset = time.time()

        self.max_requests = 55
        self.request_period = 60

    async def close(self):
        """
        Closes the client resources.

        This must be called once the client is no longer in use.
        """
        await self.session.close()

    async def check_ratelimit(self):
        async with self.lock:
            elapsed = self.last_reset - time.time()

            if elapsed >= self.request_period:
                self.requests = 0

            if self.requests >= self.max_requests - 1:
                await self.wait_for_ratelimit_end()

    async def wait_for_ratelimit_end(self):
        for count in range(1, 6):
            wait_amount = 2 ** count

            logger.warning(
                "Slow down, you are about to be rate limited. "
                f"Trying again in {wait_amount} seconds."
            )
            await asyncio.sleep(wait_amount)

            if self.requests != self.max_requests - 1:
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

    async def fetch_users(self, guild_id: int, user_ids: List[int]) -> Users:
        """
        Fetches multiple users from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the user from.
        user_ids: List[int]
            The IDs of the users you would like to fetch.
        """
        converted_user_ids = [str(user_id) for user_id in user_ids]

        body = {"members": converted_user_ids}
        data = await self.request(
            f"guild/{guild_id}/members",
            method="POST",
            extra_headers={"Content-Type": "application/json"},
            json=body,
        )

        return Users(guild_id, data)

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

        data = await self.request(f"guild/raw/{lb_type}/{guild_id}")

        return Leaderboard(guild_id, data)

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
                message = (await response.json())["error"]
            except Exception:
                message = await response.text()
            raise error(response, message)

    async def request(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        params: Dict = {},
        json: Dict = {},
        extra_headers: Dict = {},
    ) -> Dict:

        headers = dict(self._default_headers, **extra_headers)

        if self.useantiratelimit:
            await self.check_ratelimit()

        async with self.session.request(
            method=method, url=self.BASE_URL + endpoint, json=json, headers=headers, params=params
        ) as response:
            if self.useantiratelimit:
                self.requests += 1

            await self.check_response_for_errors(response)

            return await response.json()
