"""Custom exception hierarchy for Career OS."""

from typing import Any, Optional


class AppError(Exception):
    """Base class for expected application errors."""

    status_code = 500
    message = "Internal application error"

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details: dict[str, Any] = {}


class NotFoundError(AppError):
    """A requested resource does not exist."""

    status_code = 404
    message = "Resource not found"


class ValidationAppError(AppError):
    """A request or input failed validation."""

    status_code = 400
    message = "Validation error"


class ImportFailedError(AppError):
    """An import job could not be processed."""

    status_code = 422
    message = "Import failed"
