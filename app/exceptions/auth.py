from fastapi import status as http_status

from app.exceptions.base import DomainException


class AuthException(DomainException):
    """Authentication / authorization flow error"""


class InvalidCredentials(AuthException):
    error_type = "invalid_credentials"
    http_status = http_status.HTTP_401_UNAUTHORIZED
    message = "Username or password is invalid"


class AccountDisabled(AuthException):
    error_type = "account_disabled"
    http_status = http_status.HTTP_403_FORBIDDEN
    message = "User account is disabled"


class InvalidRefreshToken(AuthException):
    error_type = "invalid_refresh_token"
    http_status = http_status.HTTP_401_UNAUTHORIZED
    message = "Refresh token is invalid or revoked"


class RefreshTokenExpired(AuthException):
    error_type = "refresh_token_expired"
    http_status = http_status.HTTP_401_UNAUTHORIZED
    message = "Refresh token expired"
