from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.investor_request import FundingStage, InvestorRequestStatus


class InvestorRequestCreate(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "full_name": "Asha Verma",
                    "email": "asha@example.com",
                    "phone": "+919876543210",
                    "company_name": "GreenLoop Pvt Ltd",
                    "funding_stage": "seed",
                    "funding_amount": 5000000,
                    "currency": "INR",
                    "description": (
                        "We are building a recycling marketplace and are "
                        "raising seed funding to expand to five new cities."
                    ),
                }
            ]
        },
    )

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, pattern=r"^\+?\d{10,15}$")
    company_name: str = Field(min_length=2, max_length=200)
    funding_stage: FundingStage
    funding_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="INR", pattern=r"^[A-Za-z]{3}$")
    description: str = Field(min_length=20, max_length=2000)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: InvestorRequestStatus | None
    to_status: InvestorRequestStatus
    changed_by: UUID
    note: str | None
    changed_at: datetime


class InvestorRequestBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    phone: str | None
    company_name: str
    funding_stage: FundingStage
    funding_amount: Decimal
    currency: str
    description: str
    status: InvestorRequestStatus
    created_at: datetime
    updated_at: datetime


class InvestorRequestCreateResponse(BaseModel):
    """Shape returned right after submission (see PRD 9.3)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: InvestorRequestStatus
    full_name: str
    company_name: str
    funding_stage: FundingStage
    funding_amount: Decimal
    currency: str
    created_at: datetime


class InvestorRequestOwnerOut(InvestorRequestBaseOut):
    """What the owning user sees (no admin-only fields)."""

    status_history: list[StatusHistoryOut] = Field(default_factory=list)


class InvestorRequestOwnerListItem(InvestorRequestBaseOut):
    """Compact row for the owner's list endpoint."""


class InvestorRequestAdminOut(InvestorRequestBaseOut):
    """Full detail for admins, including review metadata and history."""

    user_id: UUID
    admin_notes: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    status_history: list[StatusHistoryOut] = Field(default_factory=list)


class InvestorRequestAdminListItem(InvestorRequestBaseOut):
    user_id: UUID
    admin_notes: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None


class StatusUpdateRequest(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "status": "under_review",
                    "admin_notes": "Reviewing financials, will respond within a week.",
                },
                {
                    "status": "rejected",
                    "admin_notes": "Market size too small for our thesis.",
                },
            ]
        },
    )

    status: InvestorRequestStatus
    admin_notes: str | None = Field(default=None, min_length=1, max_length=5000)


__all__ = [
    "InvestorRequestAdminListItem",
    "InvestorRequestAdminOut",
    "InvestorRequestCreate",
    "InvestorRequestCreateResponse",
    "InvestorRequestOwnerListItem",
    "InvestorRequestOwnerOut",
    "StatusHistoryOut",
    "StatusUpdateRequest",
]
