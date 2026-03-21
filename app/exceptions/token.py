from app.exceptions.base import DomainException


class TokenException(DomainException):
    pass


class TokenNotFound(TokenException):
    error_type = "token_not_found"
    http_status = 404
    message = "Token not found"


class TokenRevoked(TokenException):
    error_type = "token_revoked"
    http_status = 401
    message = "Token revoked"


class TokenExpired(TokenException):
    error_type = "token_expired"
    http_status = 401
    message = "Token expired"


class TokenFormatInvalid(TokenException):
    error_type = "token_format_invalid"
    http_status = 400
    message = "Token format is invalid"


class TokenValidatorMismatch(TokenException):
    error_type = "token_validator_mismatch"
    http_status = 400
    message = "Token validator mismatch"


class TokenCreationFailed(TokenException):
    error_type = "token_creation_failed"
    http_status = 409
    message = "Token creation failed"
