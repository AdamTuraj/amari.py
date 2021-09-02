from typing import Optional

import aiohttp

__all__ = (
    "AmariException",
    "HTTPException",
    "NotFound",
    "InvalidToken",
    "RatelimitException",
    "AmariServerError",
)


class AmariException(Exception):
    """Base module Exception class."""


class HTTPException(AmariException):
    """Base Exception for HTTP errors."""

    def __init__(self, response: aiohttp.ClientResponse, message: Optional[str] = None):
        self.status: int = response.status
        self.response: aiohttp.ClientResponse = response
        message = f"({self.status}): {message}" if message else f"({self.status})"
        super().__init__(message)


class NotFound(HTTPException):
    """Raised when the guild or user is not found."""

    def __init__(
        self,
        response: aiohttp.ClientResponse,
        message: Optional[str] = "Guild or user was not found.",
    ):
        super().__init__(response, message)


class InvalidToken(HTTPException):
    """Raised when the authentication key is invalid."""

    def __init__(self, response: aiohttp.ClientResponse, message: Optional[str] = None):
        super().__init__(
            response,
            "Please enter a valid authentication key.\n"
            "You can obtain your key at https://amaribot.com/developer/yourid",
        )


class RatelimitException(HTTPException):
    """Raised when ratelimit responses are recieved."""

    def __init__(
        self,
        response: aiohttp.ClientResponse,
        message: Optional[str] = "Slow down! You are being ratelimited!",
    ):
        super().__init__(response, message)


class AmariServerError(HTTPException):
    """Raised when their is an internal error in the Amari servers."""

    def __init__(
        self,
        response: aiohttp.ClientResponse,
        message: Optional[str] = "There was an internal error in the Amari servers.",
    ):
        super().__init__(response, message)
