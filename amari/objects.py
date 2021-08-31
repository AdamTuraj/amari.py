class User:
    __slots__ = ("id", "name", "exp", "level", "weeklyexp")

    def __init__(self, data):
        self.set_data(data)

    def __str__(self) -> str:
        return self.name

    def set_data(self, data):
        self.id = int(data["id"])
        self.name = data["username"]
        self.exp = int(data["exp"])
        self.level = int(data["level"])
        self.weeklyexp = int(data["weeklyExp"])


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
