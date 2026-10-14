from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.api.deps import CurrentUser, DbSession
from app.models.investor_request import InvestorRequestStatus
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.investor_request import (
    InvestorRequestCreate,
    InvestorRequestCreateResponse,
    InvestorRequestOwnerListItem,
    InvestorRequestOwnerOut,
)
from app.services import investor_request_service

router = APIRouter(prefix="/investor-requests", tags=["Investor Requests"])


@router.post(
    "",
    response_model=InvestorRequestCreateResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Submit an investor / funding request",
)
def submit_request(
    payload: InvestorRequestCreate, db: DbSession, current_user: CurrentUser
) -> InvestorRequestCreateResponse:
    request = investor_request_service.create_request(db, current_user, payload)
    return InvestorRequestCreateResponse.model_validate(request)


@router.get(
    "/me",
    response_model=Page[InvestorRequestOwnerListItem],
    summary="List my own investor requests",
)
def list_my_requests(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    status: InvestorRequestStatus | None = None,
) -> Page[InvestorRequestOwnerListItem]:
    items, total = investor_request_service.list_user_requests(
        db,
        current_user,
        status=status,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return paginate(
        [InvestorRequestOwnerListItem.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
    )


@router.get(
    "/{request_id}",
    response_model=InvestorRequestOwnerOut,
    summary="Get one of my investor requests, including status history",
)
def get_my_request(
    request_id: UUID, db: DbSession, current_user: CurrentUser
) -> InvestorRequestOwnerOut:
    request = investor_request_service.get_request_for_user(
        db, request_id, current_user
    )
    return InvestorRequestOwnerOut.model_validate(request)
