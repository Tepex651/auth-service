from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

if TYPE_CHECKING:
    pass


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint("resource", "action", name="uq_permission_resource_action"),)

    @property
    def code(self) -> str:
        return f"{self.resource}:{self.action}"
