from email.message import EmailMessage

from app.clients.smtp_client import SMTPClient


class EmailNotification:
    def __init__(self, email_client: SMTPClient) -> None:
        self.email_client = email_client

    def _build_message(self, subject: str, to: str, body: str) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["To"] = to
        message["From"] = "noreply@yourdomain.com"
        message.set_content(body)

        return message

    async def send_refresh_password_email(self, to: str, token: str) -> None:
        message = self._build_message(
            subject="Reset your password",
            to=to,
            body=f"Click the link to reset your password: http://127.0.0.1:8000/api/v1/auth/confirm-reset-password?token={token}",
        )
        await self.email_client.send(message)

    async def send_verification_email(self, to: str, token: str) -> None:
        message = self._build_message(
            subject="Verify your email address",
            to=to,
            body=f"Click the link to verify your email: http://127.0.0.1:8000/api/v1/auth/confirm-email?token={token}",
        )
        await self.email_client.send(message)
