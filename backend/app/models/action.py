import enum
from typing import Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class ModerationActionType(str, enum.Enum):
    ASSIGN = "assign"
    APPROVE = "approve"
    REJECT = "reject"
    MARK_DUPLICATE = "mark_duplicate"
    REQUEST_INFORMATION = "request_information"
    EDIT = "edit"


class ModerationAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moderation_actions"

    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_requests.id", ondelete="CASCADE"),
        index=True,
    )

    moderator_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    action: Mapped[ModerationActionType] = mapped_column(
        Enum(
            ModerationActionType,
            name="moderation_action_type",
            values_callable=enum_values,
        ),
    )

    comment: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
