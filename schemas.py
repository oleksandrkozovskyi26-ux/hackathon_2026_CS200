from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Member(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_name: str
    first_name: str | None = None
    telegram_id: int | None = None
    is_paid_current_month: bool = False