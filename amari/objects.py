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
    __slots__ = ("guild_id", "user_count", "total_count", "users")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.user_count: int = data["user_count"]
        self.total_count: int = data["total_count"]
        self.users: Dict[int, User] = {
            int(user_data["id"]): User(guild_id, user_data, i, leaderboard=self)
            for i, user_data in enumerate(data["data"])
        }

    def __repr__(self) -> str:
        return f"<Leaderboard guild_id={self.guild_id} total_count={self.total_count}>"

    def __len__(self) -> int:
        return self.user_count

    def __iter__(self) -> Iterator[User]:
        yield from self.users.copy().values()

    def get_user(self, user_id: int, /) -> Optional[User]:
        return self.users.get(user_id)


class RewardRole(_SlotsReprMixin):
    __slots__ = ("role_id", "level", "rewards")

    def __init__(self, role_id: int, level: int, rewards):
        self.role_id: int = role_id
        self.level: int = level
        self.rewards = rewards


class Rewards:
    __slots__ = ("guild_id", "reward_count", "roles")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.reward_count: int = int(data["count"])
        self.roles: Dict[int, RewardRole] = {}
        for role_data in data["data"]:
            role_id = int(role_data["roleID"])
            self.roles[role_id] = RewardRole(role_id, role_data["level"], self)

    def __repr__(self) -> str:
        return f"<Rewards guild_id={self.guild_id} reward_count={self.reward_count}>"

    def __len__(self) -> int:
        return self.reward_count

    def __iter__(self) -> Iterator[RewardRole]:
        yield from self.roles.copy().values()

    def get_role(self, role_id: int, /) -> Optional[RewardRole]:
        return self.roles.get(role_id)
