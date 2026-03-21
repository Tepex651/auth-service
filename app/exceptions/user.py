from app.exceptions.base import DomainException


class UserException(DomainException):
    pass


class UserNotFound(UserException):
    error_type = "user_not_found"
    http_status = 404


class UserAlreadyExists(UserException):
    error_type = "user_already_exists"
    http_status = 409


class RoleNotFound(UserException):
    error_type = "role_not_found"
    http_status = 404


class InvalidCurrentPassword(UserException):
    error_type = "invalid_current_password"
    http_status = 401
