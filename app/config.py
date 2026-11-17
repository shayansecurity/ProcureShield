from __future__ import annotations

import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "scoring.yaml"
DATA_PATH = ROOT / "data" / "suppliers.csv"
DB_PATH = ROOT / "data" / "procureshield.db"
KB_DIR = ROOT / "knowledge_base"
CHROMA_DIR = ROOT / "data" / "chroma"


def load_scoring_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
