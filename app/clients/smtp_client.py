from email.message import EmailMessage

import aiosmtplib


class SMTPClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def send(self, message: EmailMessage) -> None:
        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )
