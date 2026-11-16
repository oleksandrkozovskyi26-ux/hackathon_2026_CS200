from __future__ import annotations

from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class Member(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_name: str
    first_name: str | None = None
    telegram_id: int | None = None
    is_paid_current_month: bool = False


class MemberDuty(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_name: str
    first_name: str | None = None
    telegram_id: int | None = None
    duty_dates: list[date] = Field(default_factory=list)