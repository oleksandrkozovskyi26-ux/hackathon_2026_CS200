import json
import threading
from datetime import date, datetime
from pathlib import Path

from schemas import Member, MemberDuty


class DutyService:
    """Сервіс для роботи з графіком чергувань (кнопки 'Таблиця Чергування' та 'Моє чергування')."""

    def __init__(
        self,
        duty_json_path: str | Path = "api_to_json_cherguvania.json",
        members_state_path: str | Path = "members.json",
    ) -> None:
        self._duty_path = Path(duty_json_path)
        self._members_path = Path(members_state_path)
        self._lock = threading.Lock()
        self._duties: dict[str, list[date]] = {}

        self.sync_from_json()

    def sync_from_json(self) -> None:
        """Перечитує JSON з датами чергувань."""
        with self._lock:
            if not self._duty_path.exists():
                return

            raw_data: dict[str, list[str]] = json.loads(
                self._duty_path.read_text(encoding="utf-8")
            )
            parsed_duties: dict[str, list[date]] = {}

            for raw_last_name, date_strings in raw_data.items():
                last_name = raw_last_name.strip().rstrip(".")
                dates = [
                    datetime.strptime(d.strip(), "%d.%m.%Y").date()
                    for d in date_strings
                    if d.strip()
                ]
                parsed_duties[last_name] = sorted(dates)

            self._duties = parsed_duties

    def _load_registered_members(self) -> dict[str, Member]:
        """Підтягує прив'язаних користувачів із members.json."""
        if not self._members_path.exists():
            return {}
        raw_members = json.loads(self._members_path.read_text(encoding="utf-8"))
        return {
            last_name: Member.model_validate(data)
            for last_name, data in raw_members.items()
        }

    # --- Публічні методи для двох кнопок у bot.py ---

    def get_all_duties(self) -> list[MemberDuty]:
        """Для кнопки 'Таблиця Чергування' (callback_data='table_on_duty')."""
        with self._lock:
            registered = self._load_registered_members()
            result: list[MemberDuty] = []

            for last_name, dates in self._duties.items():
                member = registered.get(last_name)
                result.append(
                    MemberDuty(
                        last_name=last_name,
                        first_name=member.first_name if member else None,
                        telegram_id=member.telegram_id if member else None,
                        duty_dates=dates,
                    )
                )
            return result

    def get_duties_by_telegram_id(
        self,
        telegram_id: int,
        only_upcoming: bool = False,
        reference_date: date | None = None,
    ) -> MemberDuty | None:
        """
        Для кнопки 'Перевірити коли моє чергування' (callback_data='check_my_duty').
        Повертає MemberDuty або None, якщо користувач не зареєстрований.
        """
        with self._lock:
            registered = self._load_registered_members()
            target_member = next(
                (m for m in registered.values() if m.telegram_id == telegram_id),
                None,
            )
            if target_member is None:
                return None

            dates = self._duties.get(target_member.last_name, [])
            if only_upcoming:
                today = reference_date or date.today()
                dates = [d for d in dates if d >= today]

            return MemberDuty(
                last_name=target_member.last_name,
                first_name=target_member.first_name,
                telegram_id=target_member.telegram_id,
                duty_dates=dates,
            )