from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.models.conversation import ConversationMode
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.conversation import ConversationOut
from app.services import conversation_service

router = APIRouter(tags=["Conversations"])


@router.get(
    "/conversations",
    response_model=Page[ConversationOut],
    summary="List published conversations (public)",
)
def list_conversations(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    when: str = Query(
        "upcoming",
        pattern="^(upcoming|past)$",
        description="Filter by upcoming or past conversations",
    ),
    mode: ConversationMode | None = Query(
        None, description="Filter by mode: online or offline"
    ),
    search: str | None = Query(None, max_length=200, description="Match on title"),
) -> Page[ConversationOut]:
    items, total = conversation_service.list_public_conversations(
        db,
        when=when,
        mode=mode,
        search=search,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return paginate(
        [ConversationOut.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationOut,
    summary="Get a published conversation (public)",
)
def get_conversation(conversation_id: UUID, db: DbSession) -> ConversationOut:
    conversation = conversation_service.get_public_conversation(db, conversation_id)
    return ConversationOut.model_validate(conversation)
