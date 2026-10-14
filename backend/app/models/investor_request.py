import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import enum_values


class FundingStage(str, enum.Enum):
    IDEA = "idea"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B_PLUS = "series_b_plus"


class InvestorRequestStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class InvestorRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "investor_requests"
    __table_args__ = (
        Index("ix_investor_requests_user_id", "user_id"),
        Index("ix_investor_requests_status_created_at", "status", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    funding_stage: Mapped[FundingStage] = mapped_column(
        Enum(
            FundingStage,
            name="funding_stage",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
    )
    funding_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InvestorRequestStatus] = mapped_column(
        Enum(
            InvestorRequestStatus,
            name="investor_request_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=InvestorRequestStatus.PENDING,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at = mapped_column(DateTime(timezone=True), nullable=True)

    status_history: Mapped[list["InvestorRequestStatusHistory"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="InvestorRequestStatusHistory.changed_at",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InvestorRequest {self.company_name!r} [{self.status.value}]>"


class InvestorRequestStatusHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "investor_request_status_history"

    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investor_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[InvestorRequestStatus | None] = mapped_column(
        Enum(
            InvestorRequestStatus,
            name="investor_request_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=True,
    )
    to_status: Mapped[InvestorRequestStatus] = mapped_column(
        Enum(
            InvestorRequestStatus,
            name="investor_request_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at = mapped_column(DateTime(timezone=True), nullable=False)

    request: Mapped[InvestorRequest] = relationship(back_populates="status_history")

    def __repr__(self) -> str:
        return f"<StatusHistory {self.from_status} -> {self.to_status}>"
