from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContributionStatus(str, Enum):
    PAID = "paid"
    EXEMPT = "exempt"
    PENDING = "pending"


class MemberRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"


class MonthPayment(BaseModel):
    model_config = ConfigDict(frozen=True)

    month_number: int = Field(ge=1, le=12)
    year: int | None = None
    paid_amount: Decimal | None = None
    contribution_status: ContributionStatus


class Member(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_name: str
    first_name: str | None = None
    telegram_id: int | None = None
    telegram_username: str | None = None
    role: MemberRole = MemberRole.MEMBER
    monthly_payments: dict[tuple[int, int], MonthPayment] = Field(default_factory=dict)


class ExpenseRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: int
    item_description: str
    responsible_member_name: str
    expense_amount: Decimal
    purchase_date: date | None = None
    additional_note: str | None = None

    @field_validator("responsible_member_name", mode="before")
    @classmethod
    def normalize_member_name(cls, value: Any) -> str:
        return str(value).strip().rstrip(".")


class BudgetSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_collected: Decimal = Decimal("0.00")
    jar_balance: Decimal = Decimal("0.00")
    total_expenses: Decimal = Decimal("0.00")


class ColivingBudgetData(BaseModel):
    model_config = ConfigDict(frozen=True)

    members_by_last_name: dict[str, Member]
    expense_records: list[ExpenseRecord] = Field(default_factory=list)
    summary: BudgetSummary = Field(default_factory=BudgetSummary)
    admin_telegram_ids: frozenset[int] = Field(default_factory=frozenset)