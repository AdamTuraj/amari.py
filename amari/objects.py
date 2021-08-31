__all__ = ("User", "Leaderboard", "Rewards")

class User:
    __slots__ = ("guild_id", "user_id", "name", "exp", "level", "weeklyexp")

    def __init__(self, guild_id: int, data: dict):
        self.guild_id: int = guild_id
        self.user_id: int = int(data["id"])
        self.name: str = data["username"]
        self.exp: int = int(data["exp"])
        self.level: int = int(data["level"])
        self.weeklyexp: int = int(data["weeklyExp"])



class Leaderboard:
    __slots__ = ("id", "usercount", "leaderboard")

    def __init__(self, data):
        self.set_data(data)

    def __str__(self) -> str:
        return str(self.id)

    def set_data(self, data):
        self.id = int(data["id"])
        self.usercount = int(data["total_count"])
        self.leaderboard = data["data"]


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
