from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import AdminUser, DbSession
from app.models.investor_request import FundingStage, InvestorRequestStatus
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.investor_request import (
    InvestorRequestAdminListItem,
    InvestorRequestAdminOut,
    StatusUpdateRequest,
)
from app.services import investor_request_service

router = APIRouter(
    prefix="/admin/investor-requests",
    tags=["Admin - Investor Requests"],
)


@router.get(
    "",
    response_model=Page[InvestorRequestAdminListItem],
    summary="List all investor requests (admin)",
)
def list_requests(
    db: DbSession,
    admin: AdminUser,
    pagination: Annotated[PaginationParams, Depends()],
    status: InvestorRequestStatus | None = None,
    funding_stage: FundingStage | None = None,
    from_date: date | None = Query(
        None, description="Only requests created on or after this date (UTC)"
    ),
    to_date: date | None = Query(
        None, description="Only requests created on or before this date (UTC)"
    ),
    search: str | None = Query(
        None, max_length=200, description="Match company name or full name"
    ),
) -> Page[InvestorRequestAdminListItem]:
    items, total = investor_request_service.list_admin_requests(
        db,
        status=status,
        funding_stage=funding_stage,
        from_date=from_date,
        to_date=to_date,
        search=search,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return paginate(
        [InvestorRequestAdminListItem.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
    )


@router.get(
    "/{request_id}",
    response_model=InvestorRequestAdminOut,
    summary="Get full detail of an investor request, including status history",
)
def get_request(
    request_id: UUID, db: DbSession, admin: AdminUser
) -> InvestorRequestAdminOut:
    request = investor_request_service.get_request_or_404(db, request_id)
    return InvestorRequestAdminOut.model_validate(request)


@router.patch(
    "/{request_id}/status",
    response_model=InvestorRequestAdminOut,
    summary="Change an investor request's status (writes a history row)",
)
def update_status(
    request_id: UUID,
    payload: StatusUpdateRequest,
    db: DbSession,
    admin: AdminUser,
) -> InvestorRequestAdminOut:
    request = investor_request_service.get_request_or_404(db, request_id)
    updated = investor_request_service.change_status(
        db,
        request,
        admin,
        status=payload.status,
        admin_notes=payload.admin_notes,
    )
    return InvestorRequestAdminOut.model_validate(updated)
