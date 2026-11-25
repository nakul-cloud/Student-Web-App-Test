"""Custom application exceptions."""


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str = "Application error", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
