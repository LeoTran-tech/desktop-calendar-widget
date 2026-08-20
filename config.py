import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "Không tìm thấy config.json. Hãy copy config.example.json thành config.json."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)
