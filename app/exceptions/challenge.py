from app.exceptions.base import DomainException


class ChallengeException(DomainException):
    pass


class ChallengeNotFound(ChallengeException):
    error_type = "challenge_not_found"
    http_status = 404
    message = "Challenge not found"


class ChallengeAlreadyConsumed(ChallengeException):
    error_type = "challenge_already_consumed"
    http_status = 400
    message = "Challenge already consumed"


class ChallengeNotFoundOrConsumed(ChallengeException):
    error_type = "challenge_not_found_or_consumed"
    http_status = 404
    message = "Challenge not found or consumed"


class ChallengeExpired(ChallengeException):
    error_type = "challenge_expired"
    http_status = 400
    message = "Challenge expired"


class InvalidChallengeToken(ChallengeException):
    error_type = "invalid_challenge_token"
    http_status = 400
    message = "Challenge token is invalid"


class ChallengeCreationFailed(ChallengeException):
    error_type = "challenge_creation_failed"
    http_status = 500
    message = "Challenge create failed"


class UnsupportedChallengeType(ChallengeException):
    error_type = "unsupported_challenge_type"
    http_status = 400
    message = "Unsupporded challenge type"
