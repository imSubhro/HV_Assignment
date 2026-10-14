from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from fastapi import status as http_status

from app.api.deps import AdminUser, DbSession
from app.models.conversation import ConversationStatus
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
)
from app.services import conversation_service

router = APIRouter(
    prefix="/admin/conversations",
    tags=["Admin - Conversations"],
)


@router.post(
    "",
    response_model=ConversationOut,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a conversation (always starts as draft)",
)
def create_conversation(
    payload: ConversationCreate, db: DbSession, admin: AdminUser
) -> ConversationOut:
    conversation = conversation_service.create_conversation(db, admin, payload)
    return ConversationOut.model_validate(conversation)


@router.get(
    "",
    response_model=Page[ConversationOut],
    summary="List conversations, any status (admin)",
)
def list_conversations(
    db: DbSession,
    admin: AdminUser,
    pagination: Annotated[PaginationParams, Depends()],
    status: ConversationStatus | None = None,
    when: str | None = None,
    search: str | None = None,
) -> Page[ConversationOut]:
    items, total = conversation_service.list_admin_conversations(
        db,
        status=status,
        when=when,
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
    "/{conversation_id}",
    response_model=ConversationOut,
    summary="Get any conversation (admin)",
)
def get_conversation(
    conversation_id: UUID, db: DbSession, admin: AdminUser
) -> ConversationOut:
    conversation = conversation_service.get_conversation_or_404(db, conversation_id)
    return ConversationOut.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationOut,
    summary="Partially update a conversation (status is unchanged)",
)
def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    db: DbSession,
    admin: AdminUser,
) -> ConversationOut:
    conversation = conversation_service.update_conversation(
        db, conversation_id, payload
    )
    return ConversationOut.model_validate(conversation)


@router.post(
    "/{conversation_id}/publish",
    response_model=ConversationOut,
    summary="Publish a draft conversation",
)
def publish_conversation(
    conversation_id: UUID, db: DbSession, admin: AdminUser
) -> ConversationOut:
    conversation = conversation_service.publish_conversation(db, conversation_id)
    return ConversationOut.model_validate(conversation)


@router.post(
    "/{conversation_id}/unpublish",
    response_model=ConversationOut,
    summary="Unpublish a published conversation back to draft",
)
def unpublish_conversation(
    conversation_id: UUID, db: DbSession, admin: AdminUser
) -> ConversationOut:
    conversation = conversation_service.unpublish_conversation(db, conversation_id)
    return ConversationOut.model_validate(conversation)


@router.post(
    "/{conversation_id}/cancel",
    response_model=ConversationOut,
    summary="Cancel a draft or published conversation",
)
def cancel_conversation(
    conversation_id: UUID, db: DbSession, admin: AdminUser
) -> ConversationOut:
    conversation = conversation_service.cancel_conversation(db, conversation_id)
    return ConversationOut.model_validate(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation (speakers cascade)",
)
def delete_conversation(
    conversation_id: UUID, db: DbSession, admin: AdminUser
) -> Response:
    conversation_service.delete_conversation(db, conversation_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
