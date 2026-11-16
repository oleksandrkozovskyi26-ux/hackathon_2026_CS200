from __future__ import annotations

from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class Member(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_name: str
    first_name: str | None = None
    telegram_id: int | None = None
    is_paid_current_month: bool = False
    duty_dates: list[date] = Field(default_factory=list)

class SotnykContact(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str
    telegram_username: str | None = None
    phone: str | None = None

class WifiAccessPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    location: str | None = None  # Наприклад: "Кухня", "2-й поверх", "Основний"
    ssid: str
    password: str

class ColivingInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    coliving_name: str
    monthly_fee_uah: int
    payment_deadline_day: int = Field(ge=1, le=31)
    jar_url: str | None = None
    sotnyk: SotnykContact
    wifi_points: list[WifiAccessPoint] = Field(default_factory=list)
    duty_checklist: list[str] = Field(default_factory=list)
    house_rules: list[str] = Field(default_factory=list)