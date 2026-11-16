from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContributionStatus(str, Enum):
    """Успадкування від str дозволяє легко серіалізувати Enum у JSON та FSM бота."""
    PAID = "paid"          # Сплачено (наприклад, 200)
    EXEMPT = "exempt"      # Звільнений / вибув ("-")
    PENDING = "pending"    # Очікує оплати (порожньо / None)


class MonthPayment(BaseModel):
    model_config = ConfigDict(frozen=True)

    month_number: int = Field(ge=1, le=12)
    year: int | None = None  # На майбутнє для скейлінгу між роками
    paid_amount: Decimal | None = None
    contribution_status: ContributionStatus


class Member(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str
    telegram_id: int | None = None  # Резерв під прив'язку акаунту в Telegram-боті
    telegram_username: str | None = None
    monthly_payments: dict[int, MonthPayment] = Field(default_factory=dict)


class ExpenseRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: int  # Номер рядка або ID запису
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
    """Головний контейнер даних, готовий до передачі в хендлери Telegram-бота."""
    model_config = ConfigDict(frozen=True)

    members_by_name: dict[str, Member]
    expense_records: list[ExpenseRecord]
    summary: BudgetSummary