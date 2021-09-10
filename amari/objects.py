from __future__ import annotations

from typing import Any, Dict, Iterator, Optional, Tuple

__all__ = ("User", "Leaderboard", "RewardRole", "Rewards")


class _SlotsReprMixin:
    __slots__ = ()

    def __repr__(self) -> str:
        inner = ", ".join(
            (f"{k}={v!r}" for k, v in self.get_slotted_items() if v and not k.startswith("_"))
        )
        return f"{self.__class__.__name__}({inner})"

    def get_slotted_items(self) -> Iterator[Tuple[str, Any]]:
        for slot in self.__slots__:
            yield slot, getattr(self, slot)


class User(_SlotsReprMixin):
    """
    An Amari user.

    Attributes
    ----------
    guild_id: int
        The user's guild ID.
    user_id: int
        The user's ID.
    name: str
        The user's Discord username. This may not be up to date.
    exp: int
        The user's experience points.
    level: Optional[int]
        The user's level.
    weeklyexp: Optional[int]
        The user's weekly experience points.
    position: Optional[int]
        The user's position in the leaderboard.
    leaderboard: Optional[Leaderboard]
        The leaderboard object the user is in, if a leaderboard endpoint was fetched.
    """

    __slots__ = (
        "user_id",
        "name",
        "guild_id",
        "exp",
        "level",
        "weeklyexp",
        "position",
        "leaderboard",
    )

    def __init__(
        self,
        guild_id: int,
        data: dict,
        position: Optional[int] = None,
        *,
        leaderboard: Optional[Leaderboard] = None,
    ):
        self.guild_id: int = guild_id
        self.user_id: int = int(data["id"])
        self.name: str = data["username"]
        self.exp: int = int(data["exp"])
        self.level: Optional[int] = int(data.get("level")) if data.get("level") else None
        self.weeklyexp: Optional[int] = (
            int(data.get("weeklyExp")) if data.get("weeklyExp") else None
        )
        self.position: Optional[int] = position
        self.leaderboard = leaderboard


class Leaderboard:
    """
    An Amari leaderboard.

    Attributes
    ----------
    guild_id: int
        The guild ID.
    user_count: int
        The number of users in the leaderboard.
    total_count: Optional[int]
        The total number of users on Amari's API in this leaderboard.
    users: Dict[int, User]
        The users in the leaderboard.
    """

    __slots__ = ("guild_id", "user_count", "total_count", "users")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.user_count: int = data["count"]
        self.total_count: Optional[int] = data.get("total_count")
        self.users: Dict[int, User] = {
            int(user_data["id"]): User(guild_id, user_data, i, leaderboard=self)
            for i, user_data in enumerate(data["data"])
        }

    def __repr__(self) -> str:
        return f"<Leaderboard guild_id={self.guild_id} user_count={self.user_count}>"

    def __len__(self) -> int:
        return self.user_count

    def __iter__(self) -> Iterator[User]:
        yield from self.users.copy().values()

    def get_user(self, user_id: int, /) -> Optional[User]:
        """
        Get a user from the leaderboard.

        Parameters
        ----------
        user_id: int
            The user's ID.

        Returns
        -------
        Optional[User]
            The user, if found in the leaderboard.
        """
        return self.users.get(user_id)

    def add_user(self, user: User, /) -> Leaderboard:
        """
        Add a user to the leaderboard.

        Parameters
        ----------
        user: User
            The user to add.

        Returns
        -------
        Leaderboard
            The leaderboard the user was added to, for fluent class chaining.
        """
        self.users[user.user_id] = user
        return Leaderboard


class RewardRole(_SlotsReprMixin):
    """
    An object representing an Amari reward role.

    Attributes
    ----------
    role_id: int
        The role's ID.
    level: int
        The level that a user needs for the role to be awarded to them.
    rewards: Rewards
        The rewards object this role belongs to.
    """

    __slots__ = ("role_id", "level", "rewards")

    def __init__(self, role_id: int, level: int, rewards: Rewards):
        self.role_id: int = role_id
        self.level: int = level
        self.rewards = rewards


class Rewards:
    """
    A collection of Amari reward roles.

    Attributes
    ----------
    guild_id: int
        The guild ID.
    reward_count: int
        The number of reward roles.
    roles: Dict[int, RewardRole]
        The guild's reward roles.
    """

    __slots__ = ("guild_id", "reward_count", "roles")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.reward_count: int = int(data["count"])
        self.roles: Dict[int, RewardRole] = {}
        for role_data in data["data"]:
            role_id = int(role_data["id"])
            self.roles[role_id] = RewardRole(role_id, role_data["level"], self)

    def __repr__(self) -> str:
        return f"<Rewards guild_id={self.guild_id} reward_count={self.reward_count}>"

    def __len__(self) -> int:
        return self.reward_count

    def __iter__(self) -> Iterator[RewardRole]:
        yield from self.roles.copy().values()

    def get_role(self, role_id: int, /) -> Optional[RewardRole]:
        """
        Get a reward role from the rewards.

        Parameters
        ----------
        role_id: int
            The role's ID.

        Returns
        -------
        Optional[RewardRole]
            The role, if found in the rewards.
        """
        return self.roles.get(role_id)
