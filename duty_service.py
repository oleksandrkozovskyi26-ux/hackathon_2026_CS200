import json
import threading
from datetime import date, datetime
from pathlib import Path

from schemas import Member
from service import ColivingBudgetService


class ColivingDutyService:
    """Сервіс для збагачення members.json датами чергувань та вибірки графіку."""

    def __init__(
        self,
        duty_json_path: str | Path = "api_to_json_cherguvania.json",
        state_json_path: str | Path = "members.json",
    ) -> None:
        self._duty_path = Path(duty_json_path)
        self._state_path = Path(state_json_path)
        self._lock = threading.Lock()

        if self._duty_path.exists() and self._state_path.exists():
            self.sync_duty_dates()

    def _read_members(self) -> dict[str, Member]:
        if not self._state_path.exists():
            return {}
        raw_state = json.loads(self._state_path.read_text(encoding="utf-8"))
        return {
            last_name: Member.model_validate(member_data)
            for last_name, member_data in raw_state.items()
        }

    def _write_members(self, members: dict[str, Member]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        # mode="json" автоматично конвертує об'єкти date у рядки "YYYY-MM-DD"
        serialized = {
            last_name: member.model_dump(mode="json")
            for last_name, member in members.items()
        }
        self._state_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _parse_dates(raw_dates: list[str]) -> list[date]:
        parsed = [
            datetime.strptime(d.strip(), "%d.%m.%Y").date()
            for d in raw_dates
            if d and d.strip()
        ]
        return sorted(parsed)

    # --- Публічні методи для bot.py ---

    def sync_duty_dates(self) -> None:
        """Вписує відсортовані дати чергувань кожному учаснику в members.json."""
        with self._lock:
            if not self._duty_path.exists() or not self._state_path.exists():
                return

            members = self._read_members()
            raw_duties: dict[str, list[str]] = json.loads(
                self._duty_path.read_text(encoding="utf-8")
            )

            for raw_last_name, date_strings in raw_duties.items():
                last_name = raw_last_name.strip().rstrip(".")
                member = members.get(last_name)
                if member is None:
                    continue

                members[last_name] = member.model_copy(
                    update={"duty_dates": self._parse_dates(date_strings)}
                )

            self._write_members(members)

    def get_all_members_with_duties(self) -> list[Member]:
        """Для кнопки 'Таблиця Чергування' (callback_data='table_on_duty')."""
        with self._lock:
            return list(self._read_members().values())

    def get_my_duty_dates(
        self,
        telegram_id: int,
        only_upcoming: bool = True,
        reference_date: date | None = None,
    ) -> list[date] | None:
        """
        Для кнопки 'Перевірити коли моє чергування' (callback_data='check_my_duty').
        Повертає список дат або None, якщо користувач не зареєстрований.
        """
        today = reference_date or date.today()
        with self._lock:
            for member in self._read_members().values():
                if member.telegram_id == telegram_id:
                    if only_upcoming:
                        return [d for d in member.duty_dates if d >= today]
                    return member.duty_dates
            return None

    def get_today_duty_member(self, reference_date: date | None = None) -> Member | None:
        """Бонус: повертає чергового на сьогодні (зручно для верхівки таблиці чергувань)."""
        today = reference_date or date.today()
        with self._lock:
            for member in self._read_members().values():
                if today in member.duty_dates:
                    return member
            return None