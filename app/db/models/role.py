from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.associations import role_permissions
from app.db.models.base import Base

if TYPE_CHECKING:
    from .permission import Permission


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    permissions: Mapped[set["Permission"]] = relationship(secondary=role_permissions, lazy="selectin")
