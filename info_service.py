import json
from pathlib import Path

from schemas import ColivingInfo


class ColivingInfoService:
    """Сервіс для отримання довідкової інформації про колівінг."""

    def __init__(self, info_json_path: str | Path = "coliving_info.json") -> None:
        self._info_path = Path(info_json_path)

    def get_info(self) -> ColivingInfo:
        """Зчитує актуальну інформацію про колівінг із JSON-файлу."""
        raw_data = json.loads(self._info_path.read_text(encoding="utf-8"))
        return ColivingInfo.model_validate(raw_data)