from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base
from app.db.models.role import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="SET NULL"))
    role: Mapped[Role] = relationship("Role", lazy="selectin")

    email_confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def is_admin(self) -> bool:
        return self.role.name == "admin" if self.role else False
