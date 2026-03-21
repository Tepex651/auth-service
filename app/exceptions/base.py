class DomainException(Exception):
    """Base exception for all business errors"""

    error_type: str
    http_status: int
    message: str | None = None

    def __init__(self, message: str | None = None):
        self.message = message
        super().__init__(self.get_message())

    def get_message(self) -> str:
        if self.message:
            return self.message

        return self.error_type.replace("_", " ").capitalize()

    def __str__(self) -> str:
        return self.get_message()
