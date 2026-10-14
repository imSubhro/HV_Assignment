from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import BadRequest, NotFound
from app.models.conversation import (
    Conversation,
    ConversationMode,
    ConversationSpeaker,
    ConversationStatus,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    is_valid_http_url,
)

STATUS_TRANSITIONS: dict[ConversationStatus, set[ConversationStatus]] = {
    ConversationStatus.DRAFT: {
        ConversationStatus.PUBLISHED,
        ConversationStatus.CANCELLED,
    },
    ConversationStatus.PUBLISHED: {
        ConversationStatus.DRAFT,
        ConversationStatus.CANCELLED,
    },
    ConversationStatus.CANCELLED: set(),
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_future(scheduled_at: datetime, action: str) -> None:
    if scheduled_at <= utcnow():
        raise BadRequest(
            f"scheduled_at must be in the future when {action} a conversation",
            details=[
                {"field": "scheduled_at", "issue": "Must be a future date and time"}
            ],
        )


def validate_mode_and_location(mode: ConversationMode, location_or_link: str) -> None:
    if mode == ConversationMode.ONLINE and not is_valid_http_url(location_or_link):
        raise BadRequest(
            "location_or_link must be a valid http(s) URL when mode is 'online'",
            details=[
                {
                    "field": "location_or_link",
                    "issue": "Must be a valid http(s) URL for online conversations",
                }
            ],
        )


def _build_speakers(speakers) -> list[ConversationSpeaker]:
    return [
        ConversationSpeaker(
            name=speaker.name,
            designation=speaker.designation,
            bio=speaker.bio,
            photo_url=speaker.photo_url,
            display_order=index,
        )
        for index, speaker in enumerate(speakers)
    ]


def get_conversation_or_404(db: Session, conversation_id: UUID) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise NotFound("Conversation not found")
    return conversation


def create_conversation(
    db: Session, admin, payload: ConversationCreate
) -> Conversation:
    ensure_future(payload.scheduled_at, "creating")
    conversation = Conversation(
        title=payload.title,
        description=payload.description,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        mode=payload.mode,
        location_or_link=payload.location_or_link,
        capacity=payload.capacity,
        cover_image_url=payload.cover_image_url,
        status=ConversationStatus.DRAFT,
        created_by=admin.id,
        speakers=_build_speakers(payload.speakers),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def update_conversation(
    db: Session, conversation_id: UUID, payload: ConversationUpdate
) -> Conversation:
    conversation = get_conversation_or_404(db, conversation_id)
    data = payload.model_dump(exclude_unset=True)

    if (
        conversation.status == ConversationStatus.CANCELLED
        and "scheduled_at" in data
        and data["scheduled_at"] != conversation.scheduled_at
    ):
        raise BadRequest("Cannot reschedule a cancelled conversation")

    # `speakers` replaces the whole list only when explicitly provided.
    speakers = payload.speakers if "speakers" in payload.model_fields_set else None
    data.pop("speakers", None)
    for field, value in data.items():
        setattr(conversation, field, value)

    validate_mode_and_location(conversation.mode, conversation.location_or_link)

    if speakers is not None:
        conversation.speakers.clear()
        db.flush()
        conversation.speakers = _build_speakers(speakers)

    db.commit()
    db.refresh(conversation)
    return conversation


def list_public_conversations(
    db: Session,
    *,
    when: str,
    mode: ConversationMode | None,
    search: str | None,
    offset: int,
    limit: int,
) -> tuple[list[Conversation], int]:
    now = utcnow()
    query = db.query(Conversation).filter(Conversation.status == ConversationStatus.PUBLISHED)
    if when == "upcoming":
        query = query.filter(Conversation.scheduled_at >= now).order_by(
            Conversation.scheduled_at.asc()
        )
    else:
        query = query.filter(Conversation.scheduled_at < now).order_by(
            Conversation.scheduled_at.desc()
        )
    if mode is not None:
        query = query.filter(Conversation.mode == mode)
    if search:
        query = query.filter(Conversation.title.ilike(f"%{search.strip()}%"))

    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total


def get_public_conversation(db: Session, conversation_id: UUID) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if (
        conversation is None
        or conversation.status != ConversationStatus.PUBLISHED
    ):
        raise NotFound("Conversation not found")
    return conversation


def list_admin_conversations(
    db: Session,
    *,
    status: ConversationStatus | None,
    when: str | None,
    search: str | None,
    offset: int,
    limit: int,
) -> tuple[list[Conversation], int]:
    now = utcnow()
    query = db.query(Conversation)
    if status is not None:
        query = query.filter(Conversation.status == status)
    if when == "upcoming":
        query = query.filter(Conversation.scheduled_at >= now)
    elif when == "past":
        query = query.filter(Conversation.scheduled_at < now)
    if search:
        query = query.filter(Conversation.title.ilike(f"%{search.strip()}%"))

    query = query.order_by(Conversation.scheduled_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total


def _ensure_transition(conversation: Conversation, target: ConversationStatus) -> None:
    allowed = STATUS_TRANSITIONS[conversation.status]
    if target not in allowed:
        raise BadRequest(
            f"Cannot change a conversation from '{conversation.status.value}' "
            f"to '{target.value}'"
        )


def publish_conversation(db: Session, conversation_id: UUID) -> Conversation:
    conversation = get_conversation_or_404(db, conversation_id)
    if conversation.status != ConversationStatus.DRAFT:
        raise BadRequest(
            f"Cannot publish a {conversation.status.value} conversation"
        )
    ensure_future(conversation.scheduled_at, "publishing")
    conversation.status = ConversationStatus.PUBLISHED
    db.commit()
    db.refresh(conversation)
    return conversation


def unpublish_conversation(db: Session, conversation_id: UUID) -> Conversation:
    conversation = get_conversation_or_404(db, conversation_id)
    if conversation.status != ConversationStatus.PUBLISHED:
        raise BadRequest(
            f"Cannot unpublish a {conversation.status.value} conversation"
        )
    conversation.status = ConversationStatus.DRAFT
    db.commit()
    db.refresh(conversation)
    return conversation


def cancel_conversation(db: Session, conversation_id: UUID) -> Conversation:
    conversation = get_conversation_or_404(db, conversation_id)
    _ensure_transition(conversation, ConversationStatus.CANCELLED)
    conversation.status = ConversationStatus.CANCELLED
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation_id: UUID) -> None:
    conversation = get_conversation_or_404(db, conversation_id)
    db.delete(conversation)
    db.commit()
