from enum import StrEnum


class Environment(StrEnum):
    PROD = "prod"
    DEV = "dev"
    TEST = "test"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ChallengeType(StrEnum):
    PASSWORD_RESET = "password_reset"  # noqa: S105
    MFA_ENABLE = "mfa_enable"
    MFA_DISABLE = "mfa_disable"
    REFRESH = "refresh"
    LOGIN = "login"
    EMAIL_VERIFICATION = "email_verification"


class MFAMethods(StrEnum):
    TOTP = "TOTP"
