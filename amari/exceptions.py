class BaseHTTPRequestError(Exception):
    """Base error for request responses."""


class NotFound(BaseHTTPRequestError):
    """Raised when the guild or user is not found."""

    def __init__(self):
        super().__init__("Guild or user was not found.")


class InvalidToken(BaseHTTPRequestError):
    """Raised when the authentication key is invalid."""

    def __init__(self):
        super().__init__(
            "Please enter a valid authentication key.\n"
            "You can obtain your key at https://amaribot.com/developer/yourid"
        )


class Ratelimited(BaseHTTPRequestError):
    """Raised when ratelimit responses are recieved."""

    def __init__(self, message="Slow down! You are being ratelimited!"):
        super().__init__(message)


class AmariServerError(BaseHTTPRequestError):
    """Raised when their is an internal error in the Amari servers."""

    def __init__(self):
        super().__init__("There was an internal error in the Amari servers.")
