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
    __slots__ = ("id", "count", "roles")

    def __init__(self, data):
        self.set_data(data)

    def __str__(self) -> str:
        return str(self.id)

    def set_data(self, data):
        self.id = int(data["id"])
        self.count = int(data["count"])
        self.roles = [(role["level"], role["roleID"]) for role in data["data"]]
