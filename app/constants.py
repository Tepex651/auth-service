from enum import StrEnum


class Roles(StrEnum):
    ADMIN = "admin"
    USER = "user"


class Resources(StrEnum):
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    TOKEN = "token"  # noqa: S105


class Actions(StrEnum):
    MANAGE = "manage"
    READ = "read"
