from dataclasses import dataclass


@dataclass
class MFAEnableRequired:
    uri: str
    challenge_token: str


@dataclass
class MFAVerificationRequired:
    challenge_token: str
