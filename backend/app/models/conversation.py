import enum
import uuid

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import enum_values


class ConversationMode(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class ConversationStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_status_scheduled_at", "status", "scheduled_at"),
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[ConversationMode] = mapped_column(
        Enum(
            ConversationMode,
            name="conversation_mode",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
    )
    location_or_link: Mapped[str] = mapped_column(String(500), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(
            ConversationStatus,
            name="conversation_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=ConversationStatus.DRAFT,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    speakers: Mapped[list["ConversationSpeaker"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationSpeaker.display_order",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.title!r} [{self.status.value}]>"


class ConversationSpeaker(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "conversation_speakers"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    conversation: Mapped[Conversation] = relationship(back_populates="speakers")

    def __repr__(self) -> str:
        return f"<ConversationSpeaker {self.name!r}>"
