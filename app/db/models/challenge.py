from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    selector: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    validator_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
