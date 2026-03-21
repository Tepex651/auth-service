from fastapi import status as http_status

from app.exceptions.auth import AuthException


class MFAException(AuthException):
    error_type = "mfa_error"
    http_status = http_status.HTTP_400_BAD_REQUEST
    message = "Multi-factor authentication error"


class MFAAlreadyEnabled(MFAException):
    error_type = "mfa_already_enabled"
    http_status = http_status.HTTP_400_BAD_REQUEST
    message = "MFA already enabled"


class MFAEnableFailed(MFAException):
    error_type = "mfa_enable_failed"
    http_status = http_status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "MFA enable failed"


class MFANotFound(MFAException):
    error_type = "mfa_not_found"
    http_status = http_status.HTTP_404_NOT_FOUND
    message = "MFA not found"


class InvalidMFACode(MFAException):
    error_type = "invalid_mfa_code"
    http_status = http_status.HTTP_400_BAD_REQUEST
    message = "Invalid MFA-code"
