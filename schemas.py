from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContributionStatus(str, Enum):
    PAID = "paid"          # Сплачено (наприклад, 200)
    EXEMPT = "exempt"      # Звільнений / вибув ("-")
    PENDING = "pending"    # Очікує оплати (порожньо / None)


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

    full_name: str
    telegram_id: int | None = None
    telegram_username: str | None = None
    role: MemberRole = MemberRole.MEMBER
    monthly_payments: dict[int, MonthPayment] = Field(default_factory=dict)

    @property
    def is_admin(self) -> bool:
        return self.role == MemberRole.ADMIN


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

    total_collected: Decimal
    jar_balance: Decimal
    total_expenses: Decimal


class ColivingBudgetData(BaseModel):
    """Головний контейнер даних, який отримує розробник бізнес-логіки бота."""
    model_config = ConfigDict(frozen=True)

    members_by_name: dict[str, Member]
    expense_records: list[ExpenseRecord]
    summary: BudgetSummary
    admin_telegram_ids: frozenset[int] = Field(default_factory=frozenset)

    def get_member_by_tg_id(self, telegram_id: int) -> Member | None:
        for member in self.members_by_name.values():
            if member.telegram_id == telegram_id:
                return member
        return None

    def is_admin_tg_id(self, telegram_id: int) -> bool:
        if telegram_id in self.admin_telegram_ids:
            return True
        member = self.get_member_by_tg_id(telegram_id)
        return member is not None and member.is_admin