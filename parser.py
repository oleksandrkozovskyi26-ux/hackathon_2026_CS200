import json
from datetime import date
from pathlib import Path
from typing import Any

from schemas import Member


def _is_paid_for_month(last_paid_tag: str, target_year: int, target_month: int) -> bool:
    if not last_paid_tag or "." not in last_paid_tag:
        return False
    month_str, year_short_str = last_paid_tag.strip().split(".", 1)
    paid_year = 2000 + int(year_short_str)
    paid_month = int(month_str)
    return (paid_year, paid_month) >= (target_year, target_month)


def _load_users_by_last_name(users_data: Any) -> dict[str, dict[str, Any]]:
    """Приводить users.json (список або словник) до мапи {last_name: {telegram_id, first_name}}."""
    by_last_name: dict[str, dict[str, Any]] = {}
    if not users_data:
        return by_last_name

    # Варіант 1: список об'єктів [{"telegram_id": 123, "first_name": "Єгор", "last_name": "Бачурін"}]
    if isinstance(users_data, list):
        for user in users_data:
            last_name = str(user.get("last_name", "")).strip().rstrip(".")
            if last_name:
                by_last_name[last_name] = {
                    "telegram_id": int(user["telegram_id"]),
                    "first_name": user.get("first_name"),
                }

    # Варіант 2: словник {"123": {"first_name": "Єгор", "last_name": "Бачурін"}}
    elif isinstance(users_data, dict):
        for tg_id_str, user in users_data.items():
            last_name = str(user.get("last_name", "")).strip().rstrip(".")
            if last_name:
                by_last_name[last_name] = {
                    "telegram_id": int(user.get("telegram_id", tg_id_str)),
                    "first_name": user.get("first_name"),
                }

    return by_last_name


def build_and_save_members(
    payments_json_path: str | Path = "api_to_json.json",
    users_json_path: str | Path = "users.json",
    output_json_path: str | Path = "members.json",
    reference_date: date | None = None,
) -> dict[str, Member]:
    """
    Об'єднує api_to_json.json та users.json у словник моделей Member
    і зберігає готовий результат у output_json_path.
    """
    payments_raw: dict[str, str] = json.loads(
        Path(payments_json_path).read_text(encoding="utf-8")
    )

    users_file = Path(users_json_path)
    users_raw = (
        json.loads(users_file.read_text(encoding="utf-8"))
        if users_file.exists()
        else []
    )
    users_by_last_name = _load_users_by_last_name(users_raw)

    current_date = reference_date or date.today()
    members: dict[str, Member] = {}

    for raw_last_name, last_paid_tag in payments_raw.items():
        last_name = raw_last_name.strip().rstrip(".")
        user_info = users_by_last_name.get(last_name, {})

        members[last_name] = Member(
            last_name=last_name,
            first_name=user_info.get("first_name"),
            telegram_id=user_info.get("telegram_id"),
            is_paid_current_month=_is_paid_for_month(
                last_paid_tag=last_paid_tag,
                target_year=current_date.year,
                target_month=current_date.month,
            ),
        )

    # Збереження результату у файл
    serialized = {
        last_name: member.model_dump()
        for last_name, member in members.items()
    }
    Path(output_json_path).write_text(
        json.dumps(serialized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return members


if __name__ == "__main__":
    build_and_save_members()