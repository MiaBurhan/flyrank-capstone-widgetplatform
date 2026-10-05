"""Domain errors. Services raise these; main.py turns them into HTTP responses."""


class AppError(Exception):
    status_code = 400
    detail = "Bad request"

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class NotFoundError(AppError):
    status_code = 404
    detail = "Not found"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Forbidden"


class RateLimitedError(AppError):
    status_code = 429
    detail = "Too many requests"
