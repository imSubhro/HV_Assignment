from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.errors import BadRequest, NotFound, ValidationFailed
from app.models.investor_request import (
    InvestorRequest,
    InvestorRequestStatus,
    InvestorRequestStatusHistory,
)
from app.models.user import User, UserRole
from app.schemas.investor_request import InvestorRequestCreate

STATUS_TRANSITIONS: dict[InvestorRequestStatus, set[InvestorRequestStatus]] = {
    InvestorRequestStatus.PENDING: {
        InvestorRequestStatus.UNDER_REVIEW,
        InvestorRequestStatus.APPROVED,
        InvestorRequestStatus.REJECTED,
    },
    InvestorRequestStatus.UNDER_REVIEW: {
        InvestorRequestStatus.APPROVED,
        InvestorRequestStatus.REJECTED,
    },
    InvestorRequestStatus.APPROVED: set(),
    InvestorRequestStatus.REJECTED: set(),
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_request_or_404(db: Session, request_id: UUID) -> InvestorRequest:
    request = db.get(InvestorRequest, request_id)
    if request is None:
        raise NotFound("Investor request not found")
    return request


def get_request_for_user(
    db: Session, request_id: UUID, user: User
) -> InvestorRequest:
    """Owner or admin only; anything else is a 404 so IDs are not leaked."""
    request = db.get(InvestorRequest, request_id)
    if request is None or (
        user.role != UserRole.ADMIN and request.user_id != user.id
    ):
        raise NotFound("Investor request not found")
    return request


def create_request(
    db: Session, user: User, payload: InvestorRequestCreate
) -> InvestorRequest:
    data = payload.model_dump()
    request = InvestorRequest(
        user_id=user.id,
        status=InvestorRequestStatus.PENDING,
        **data,
    )
    request.status_history.append(
        InvestorRequestStatusHistory(
            from_status=None,
            to_status=InvestorRequestStatus.PENDING,
            changed_by=user.id,
            note=None,
            changed_at=utcnow(),
        )
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def list_user_requests(
    db: Session,
    user: User,
    *,
    status: InvestorRequestStatus | None,
    offset: int,
    limit: int,
) -> tuple[list[InvestorRequest], int]:
    query = db.query(InvestorRequest).filter(InvestorRequest.user_id == user.id)
    if status is not None:
        query = query.filter(InvestorRequest.status == status)
    query = query.order_by(InvestorRequest.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=timezone.utc)


def list_admin_requests(
    db: Session,
    *,
    status: InvestorRequestStatus | None,
    funding_stage,
    from_date: date | None,
    to_date: date | None,
    search: str | None,
    offset: int,
    limit: int,
) -> tuple[list[InvestorRequest], int]:
    if from_date is not None and to_date is not None and from_date > to_date:
        raise BadRequest("from_date must be earlier than or equal to to_date")

    query = db.query(InvestorRequest)
    if status is not None:
        query = query.filter(InvestorRequest.status == status)
    if funding_stage is not None:
        query = query.filter(InvestorRequest.funding_stage == funding_stage)
    if from_date is not None:
        query = query.filter(InvestorRequest.created_at >= _start_of_day(from_date))
    if to_date is not None:
        query = query.filter(InvestorRequest.created_at <= _end_of_day(to_date))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                InvestorRequest.company_name.ilike(term),
                InvestorRequest.full_name.ilike(term),
            )
        )

    query = query.order_by(InvestorRequest.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total


def change_status(
    db: Session,
    request: InvestorRequest,
    admin: User,
    *,
    status: InvestorRequestStatus,
    admin_notes: str | None,
) -> InvestorRequest:
    if status == InvestorRequestStatus.REJECTED and not admin_notes:
        raise ValidationFailed(
            "admin_notes is required when rejecting a request",
            details=[
                {
                    "field": "admin_notes",
                    "issue": "A rejection reason is required",
                }
            ],
        )

    if status not in STATUS_TRANSITIONS[request.status]:
        raise BadRequest(
            f"Cannot change an investor request from '{request.status.value}' "
            f"to '{status.value}'"
        )

    previous_status = request.status
    request.status = status
    if admin_notes is not None:
        request.admin_notes = admin_notes
    request.reviewed_by = admin.id
    request.reviewed_at = utcnow()
    request.status_history.append(
        InvestorRequestStatusHistory(
            from_status=previous_status,
            to_status=status,
            changed_by=admin.id,
            note=admin_notes,
            changed_at=request.reviewed_at,
        )
    )
    db.commit()
    db.refresh(request)
    return request
