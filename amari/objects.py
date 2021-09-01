__all__ = ("User", "Leaderboard", "Rewards")


class User:
    __slots__ = ("guild_id", "user_id", "name", "exp", "level", "weeklyexp", "position")

    def __init__(self, guild_id: int, data: dict, position: int = None):
        self.guild_id: int = guild_id
        self.user_id: int = int(data["id"])
        self.name: str = data["username"]
        self.exp: int = int(data["exp"])
        self.level: int = int(data.get("level")) if data.get("level") else None
        self.weeklyexp: int = (
            int(data.get("weeklyExp")) if data.get("weeklyExp") else None
        )
        self.position: int = position

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id} exp={self.exp}>"


class Leaderboard:
    __slots__ = ("guild_id", "total_count", "leaderboard")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.total_count: int = int(data["total_count"])
        self.leaderboard = [
            User(guild_id, user, position) for position, user in enumerate(data["data"])
        ]

    def __repr__(self) -> str:
        return f"<Leaderboard guild_id={self.guild_id} total_count={self.total_count}>"

    def __len__(self) -> int:
        return self.total_count


class Rewards:
    __slots__ = ("guild_id", "reward_count", "rewards")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.reward_count: int = int(data["count"])
        self.rewards = [(role["level"], role["roleID"]) for role in data["data"]]

    def __repr__(self) -> str:
        return f"<Rewards guild_id={self.guild_id} reward_count = {self.reward_count}>"

    def __len__(self) -> int:
        return self.reward_count
