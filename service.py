import json
import threading
from datetime import date
from pathlib import Path

from schemas import Member


class ColivingBudgetService:
    """Сервіс для роботи з учасниками та збереження стану в members.json."""

    def __init__(
        self,
        api_json_path: str | Path = "api_to_json_vkladka.json",
        state_json_path: str | Path = "members.json",
    ) -> None:
        self._api_path = Path(api_json_path)
        self._state_path = Path(state_json_path)
        self._lock = threading.Lock()
        self._members: dict[str, Member] = {}

        self._load_initial_state()

    def _load_initial_state(self) -> None:
        if self._state_path.exists():
            raw_state = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._members = {
                last_name: Member.model_validate(member_data)
                for last_name, member_data in raw_state.items()
            }
        if self._api_path.exists():
            self.sync_from_api_json()

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = {
            last_name: member.model_dump()
            for last_name, member in self._members.items()
        }
        self._state_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _is_paid_for_month(last_paid_tag: str, target_date: date) -> bool:
        if not last_paid_tag or "." not in last_paid_tag:
            return False
        month_str, year_short_str = last_paid_tag.strip().split(".", 1)
        paid_year = 2000 + int(year_short_str)
        paid_month = int(month_str)
        return (paid_year, paid_month) >= (target_date.year, target_date.month)

    def sync_from_api_json(self, reference_date: date | None = None) -> None:
        """Оновлює статуси оплат з api_to_json.json, зберігаючи прив'язані telegram_id."""
        with self._lock:
            if not self._api_path.exists():
                return

            raw_payments: dict[str, str] = json.loads(
                self._api_path.read_text(encoding="utf-8")
            )
            current_date = reference_date or date.today()
            updated_members: dict[str, Member] = {}

            for raw_last_name, last_paid_tag in raw_payments.items():
                last_name = raw_last_name.strip().rstrip(".")
                existing = self._members.get(last_name)

                updated_members[last_name] = Member(
                    last_name=last_name,
                    first_name=existing.first_name if existing else None,
                    telegram_id=existing.telegram_id if existing else None,
                    is_paid_current_month=self._is_paid_for_month(last_paid_tag, current_date),
                )

            self._members = updated_members
            self._save_state()

    def register_user(self, telegram_id: int, last_name: str, first_name: str) -> Member | None:
        """Реєструє користувача за прізвищем та зберігає в members.json."""
        clean_last_name = last_name.strip().rstrip(".")
        with self._lock:
            existing = self._members.get(clean_last_name)
            if existing is None:
                return None

            updated = existing.model_copy(
                update={
                    "telegram_id": telegram_id,
                    "first_name": first_name.strip(),
                }
            )
            self._members[clean_last_name] = updated
            self._save_state()
            return updated

    def get_by_telegram_id(self, telegram_id: int) -> Member | None:
        with self._lock:
            for member in self._members.values():
                if member.telegram_id == telegram_id:
                    return member
            return None

    def get_all_members(self) -> list[Member]:
        with self._lock:
            return list(self._members.values())