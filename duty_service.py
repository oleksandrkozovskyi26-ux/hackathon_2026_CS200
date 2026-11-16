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
        self._duties: dict[str, MemberDuty] = {}

        self._load_initial_state()

    def _load_initial_state(self) -> None:
        if self._state_path.exists():
            raw_state = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._duties = {
                last_name: MemberDuty.model_validate(duty_data)
                for last_name, duty_data in raw_state.items()
            }
        if self._api_path.exists():
            self.sync_from_api_json()

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        # mode="json" автоматично конвертує datetime.date у ISO-рядки для json.dumps
        serialized = {
            last_name: duty.model_dump(mode="json")
            for last_name, duty in self._duties.items()
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
        """Перечитує api_to_json_duty.json, мерджить з members.json та записує у duties.json."""
        with self._lock:
            if not self._api_path.exists():
                return

            raw_data: dict[str, list[str]] = json.loads(
                self._api_path.read_text(encoding="utf-8")
            )
            registered = self._load_registered_members()
            updated_duties: dict[str, MemberDuty] = {}

            for raw_last_name, date_strings in raw_data.items():
                last_name = raw_last_name.strip().rstrip(".")
                member = registered.get(last_name)
                existing = self._duties.get(last_name)

                dates = sorted(
                    datetime.strptime(d.strip(), "%d.%m.%Y").date()
                    for d in date_strings
                    if d.strip()
                )

                updated_duties[last_name] = MemberDuty(
                    last_name=last_name,
                    first_name=(
                        member.first_name
                        if member and member.first_name
                        else (existing.first_name if existing else None)
                    ),
                    telegram_id=(
                        member.telegram_id
                        if member and member.telegram_id
                        else (existing.telegram_id if existing else None)
                    ),
                    duty_dates=dates,
                )

            self._duties = updated_duties
            self._save_state()

    def get_all_duties(self) -> list[MemberDuty]:
        """Для кнопки 'Таблиця Чергування' (callback_data='table_on_duty')."""
        with self._lock:
            return list(self._duties.values())

    def get_duties_by_telegram_id(
        self,
        telegram_id: int,
        only_upcoming: bool = False,
        reference_date: date | None = None,
    ) -> MemberDuty | None:
        """Для кнопки 'Перевірити коли моє чергування' (callback_data='check_my_duty')."""
        with self._lock:
            # Якщо користувач зареєструвався вже після старту бота, підтягуємо свіжий telegram_id
            target_duty = next(
                (d for d in self._duties.values() if d.telegram_id == telegram_id),
                None,
            )
            if target_duty is None:
                registered = self._load_registered_members()
                member = next(
                    (m for m in registered.values() if m.telegram_id == telegram_id),
                    None,
                )
                if member is None or member.last_name not in self._duties:
                    return None

                target_duty = self._duties[member.last_name].model_copy(
                    update={
                        "first_name": member.first_name,
                        "telegram_id": member.telegram_id,
                    }
                )
                self._duties[member.last_name] = target_duty
                self._save_state()

            if only_upcoming:
                today = reference_date or date.today()
                upcoming_dates = [d for d in target_duty.duty_dates if d >= today]
                return target_duty.model_copy(update={"duty_dates": upcoming_dates})

            return target_duty