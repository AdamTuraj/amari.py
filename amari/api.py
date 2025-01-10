import asyncio
import logging
import time
from typing import Dict, List, Optional

import aiohttp

from .cache import Cache
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

    max_requests: int
        The number of requests that can be made per second

    cache_ttl: int
        The time to live for cache entries, in seconds.

    cache: Cache
        The cache instance used to store API responses.

    maxbytes: int
        The maximum total size of cached data in bytes.
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
        useAntirateLimit: bool = True,
        session: Optional[aiohttp.ClientSession] = None,
        max_requests: int = 55,
        cache_ttl: int = 60,
        maxbytes: int = 25 * 1024 * 1024,  # 25 MiB
    ):
        self.session = session or aiohttp.ClientSession()
        self._default_headers = {"Authorization": token}

        self.lock = asyncio.Lock()

        # Anti Ratelimit section
        self.use_anti_ratelimit = useAntirateLimit

        self.requests = []

        self.max_requests = max_requests
        self.request_period = 60
        self.cache = Cache(ttl=cache_ttl, maxbytes=maxbytes)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self):
        """
        Closes the client resources.

        This must be called once the client is no longer in use.
        """
        await self.session.close()

    async def check_ratelimit(self):
        async with self.lock:
            while len(self.requests) >= self.max_requests:
                self.requests = [
                    request
                    for request in self.requests
                    if time.time() - request < self.request_period
                ]

                if len(self.requests) >= self.max_requests:
                    await self.wait_for_ratelimit_end()

    async def wait_for_ratelimit_end(self):
        wait_amount = self.request_period - (time.time() - min(self.requests))
        logger.warning(
            f"You are about to be ratelimited! Waiting {round(wait_amount)} seconds."
        )

        await asyncio.sleep(wait_amount)

    async def fetch_user(
        self, guild_id: int, user_id: int, cache: bool = False
    ) -> User:
        """
        Fetches a user from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the user from.
        user_id: int
            The user's ID.
        cache: bool
            Whether to use caching for this request.

        Returns
        -------
        User
            The user object.
        """
        if cache:
            key = ("fetch_user", guild_id, user_id)
            data = await self.cache.get(key)
            if data:
                return User(guild_id, data)
            else:
                data = await self.request(f"guild/{guild_id}/member/{user_id}")
                await self.cache.set(key, data)
                return User(guild_id, data)
        else:
            data = await self.request(f"guild/{guild_id}/member/{user_id}")
            return User(guild_id, data)

    async def fetch_users(
        self, guild_id: int, user_ids: List[int], cache: bool = False
    ) -> Users:
        """
        Fetches multiple users from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the users from.
        user_ids: List[int]
            The IDs of the users you would like to fetch.
        cache: bool
            Whether to use caching for this request.

        Returns
        -------
        Users
            The users object containing the fetched users.
        """
        if cache:
            members = []
            uncached_user_ids = []

            for user_id in user_ids:
                key = ("fetch_user", guild_id, user_id)
                data = await self.cache.get(key)
                if data:
                    members.append(data)
                else:
                    uncached_user_ids.append(user_id)

            if uncached_user_ids:
                converted_user_ids = [str(user_id) for user_id in uncached_user_ids]
                body = {"members": converted_user_ids}
                fetched_data = await self.request(
                    f"guild/{guild_id}/members",
                    method="POST",
                    extra_headers={"Content-Type": "application/json"},
                    json=body,
                )
                for user_data in fetched_data["members"]:
                    user_id = int(user_data["id"])
                    key = ("fetch_user", guild_id, user_id)
                    await self.cache.set(key, user_data)
                    members.append(user_data)

            data = {
                "members": members,
                "total_members": len(members),
                "queried_members": len(user_ids),
            }
            return Users(guild_id, data)
        else:
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
        cache: bool = False,
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
        cache: bool
            Whether to use caching for this request.

        Returns
        -------
        Leaderboard
            The guild's leaderboard.
        """
        if cache:
            key = ("fetch_leaderboard", guild_id, weekly, raw, page, limit)
            data = await self.cache.get(key)
            if data:
                return Leaderboard(guild_id, data)
        if raw and page:
            raise ValueError("raw endpoints do not support pagination")
        params = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        lb_type = "weekly" if weekly else "leaderboard"
        endpoint = ["guild", lb_type, str(guild_id)]
        if raw:
            endpoint.insert(1, "raw")

        data = await self.request("/".join(endpoint), params=params)
        if cache:
            await self.cache.set(key, data)
        return Leaderboard(guild_id, data)

    async def fetch_full_leaderboard(
        self, guild_id: int, /, *, weekly: bool = False, cache: bool = False
    ) -> Leaderboard:
        """
        Fetches a guild's full leaderboard from the Amari API.

        Parameters
        ----------
        guild_id: int
            The guild ID to fetch the leaderboard from.
        weekly: bool
            Choose either to fetch the weekly leaderboard or the regular leaderboard.
        cache: bool
            Whether to use caching for this request.

        Returns
        -------
        Leaderboard
            The guild's leaderboard.
        """
        if cache:
            key = ("fetch_full_leaderboard", guild_id, weekly)
            data = await self.cache.get(key)
            if data:
                return Leaderboard(guild_id, data)
        lb_type = "weekly" if weekly else "leaderboard"
        data = await self.request(f"guild/raw/{lb_type}/{guild_id}")
        if cache:
            await self.cache.set(key, data)
        return Leaderboard(guild_id, data)

    async def fetch_rewards(
        self, guild_id: int, /, *, page: int = 1, limit: int = 50, cache: bool = False
    ) -> Rewards:
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
        cache: bool
            Whether to use caching for this request.

        Returns
        -------
        Rewards
            The guild's role rewards.
        """
        if cache:
            key = ("fetch_rewards", guild_id, page, limit)
            data = await self.cache.get(key)
            if data:
                return Rewards(guild_id, data)
        params = {"page": page, "limit": limit}
        data = await self.request(f"guild/rewards/{guild_id}", params=params)
        if cache:
            await self.cache.set(key, data)
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

        if self.use_anti_ratelimit:
            await self.check_ratelimit()

        async with self.session.request(
            method=method,
            url=self.BASE_URL + endpoint,
            json=json,
            headers=headers,
            params=params,
        ) as response:
            if self.use_anti_ratelimit:
                self.requests.append(time.time())

            await self.check_response_for_errors(response)

            return await response.json()
