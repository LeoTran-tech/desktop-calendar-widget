import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.json was not found. Copy config.example.json to config.json "
            "and fill in your calendar settings."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)
