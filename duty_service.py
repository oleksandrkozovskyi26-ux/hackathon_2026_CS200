import json
import threading
from datetime import date, datetime
from pathlib import Path

from schemas import Member, MemberDuty


class DutyService:
    """Сервіс для роботи з графіком чергувань та збереження стану в duties.json."""

    def __init__(
        self,
        api_duty_json_path: str | Path = "api_to_json_duty.json",
        state_json_path: str | Path = "duties.json",
        members_state_path: str | Path = "members.json",
    ) -> None:
        self._api_path = Path(api_duty_json_path)
        self._state_path = Path(state_json_path)
        self._members_path = Path(members_state_path)
        self._lock = threading.Lock()
        self._duties_by_last_name: dict[str, MemberDuty] = {}

        self._load_initial_state()

    def _load_initial_state(self) -> None:
        if self._state_path.exists():
            raw_state = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._duties_by_last_name = {
                last_name: MemberDuty.model_validate(duty_data)
                for last_name, duty_data in raw_state.items()
            }
        if self._api_path.exists():
            self.sync_from_api_json()

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        # mode="json" автоматично серіалізує об'єкти datetime.date у рядки "YYYY-MM-DD"
        serialized = {
            last_name: duty.model_dump(mode="json")
            for last_name, duty in self._duties_by_last_name.items()
        }
        self._state_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_registered_members(self) -> dict[str, Member]:
        if not self._members_path.exists():
            return {}
        raw_members = json.loads(self._members_path.read_text(encoding="utf-8"))
        return {
            last_name: Member.model_validate(data)
            for last_name, data in raw_members.items()
        }

    # --- Публічні методи для bot.py ---

    def sync_from_api_json(self) -> None:
        """Оновлює дати чергувань з api_to_json_duty.json, синхронізує профілі та зберігає у duties.json."""
        with self._lock:
            if not self._api_path.exists():
                return

            raw_data: dict[str, list[str]] = json.loads(
                self._api_path.read_text(encoding="utf-8")
            )
            registered_members = self._load_registered_members()
            updated_duties: dict[str, MemberDuty] = {}

            for raw_last_name, date_strings in raw_data.items():
                last_name = raw_last_name.strip().rstrip(".")
                dates = sorted(
                    datetime.strptime(d.strip(), "%d.%m.%Y").date()
                    for d in date_strings
                    if d.strip()
                )
                member = registered_members.get(last_name)
                existing_duty = self._duties_by_last_name.get(last_name)

                updated_duties[last_name] = MemberDuty(
                    last_name=last_name,
                    first_name=(
                        member.first_name
                        if member and member.first_name
                        else (existing_duty.first_name if existing_duty else None)
                    ),
                    telegram_id=(
                        member.telegram_id
                        if member and member.telegram_id
                        else (existing_duty.telegram_id if existing_duty else None)
                    ),
                    duty_dates=dates,
                )

            self._duties_by_last_name = updated_duties
            self._save_state()

    def get_all_duties(self) -> list[MemberDuty]:
        """Для кнопки 'Таблиця Чергування' (table_on_duty)."""
        with self._lock:
            return list(self._duties_by_last_name.values())

    def get_duties_by_telegram_id(
        self,
        telegram_id: int,
        only_upcoming: bool = False,
        reference_date: date | None = None,
    ) -> MemberDuty | None:
        """Для кнопки 'Перевірити коли моє чергування' (check_my_duty)."""
        with self._lock:
            # Якщо користувач зареєструвався вже після створення duties.json — підтягуємо свіжий members.json
            registered = self._load_registered_members()
            target_member = next(
                (m for m in registered.values() if m.telegram_id == telegram_id),
                None,
            )
            if target_member is None:
                return None

            duty = self._duties_by_last_name.get(target_member.last_name)
            if duty is None:
                return None

            # Якщо в duties.json ще не було telegram_id — оновлюємо і зберігаємо у файл
            if duty.telegram_id != telegram_id or duty.first_name != target_member.first_name:
                duty = duty.model_copy(
                    update={
                        "telegram_id": target_member.telegram_id,
                        "first_name": target_member.first_name,
                    }
                )
                self._duties_by_last_name[target_member.last_name] = duty
                self._save_state()

            if only_upcoming:
                today = reference_date or date.today()
                upcoming_dates = [d for d in duty.duty_dates if d >= today]
                return duty.model_copy(update={"duty_dates": upcoming_dates})

            return duty