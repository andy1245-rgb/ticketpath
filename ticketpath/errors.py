"""The one error type the HTTP layer understands.

Raised by the api modules and the orchestrator, caught by the server, turned into
a JSON body with a `message` (the frontend surfaces that string) and a `status`.
"""

from __future__ import annotations


class ApiError(Exception):
    """An error that has a place on the wire."""

    def __init__(self, status: int, message: str, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code

    def payload(self) -> dict:
        body = {"message": self.message, "status": self.status}
        if self.code:
            body["code"] = self.code
        return body


def not_found(what: str, identifier: str) -> ApiError:
    """404, not 200-with-null: the frontend renders its not-found page from this."""
    return ApiError(404, f"{what} {identifier} not found", "not_found")


def bad_request(message: str, code: str = "bad_request") -> ApiError:
    return ApiError(400, message, code)
