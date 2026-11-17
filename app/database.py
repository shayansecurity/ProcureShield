from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    overall_score REAL NOT NULL,
    tier TEXT NOT NULL,
    domain_scores_json TEXT NOT NULL,
    top_drivers_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    brief_text TEXT NOT NULL,
    model_version TEXT NOT NULL
);
"""


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path | str = DB_PATH) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def save_assessment(
    supplier: dict[str, Any], score: dict[str, Any], evidence: list[dict], brief: str, path: Path | str = DB_PATH
) -> int:
    init_db(path)
    with connect(path) as conn:
        cur = conn.execute(
            """INSERT INTO assessments
            (supplier_id, supplier_name, assessed_at, overall_score, tier, domain_scores_json,
             top_drivers_json, evidence_json, brief_text, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(supplier.get("supplier_id", "")),
                str(supplier.get("supplier_name", "")),
                datetime.now(timezone.utc).isoformat(),
                float(score["overall_score"]),
                str(score["tier"]),
                json.dumps(score["domain_scores"]),
                json.dumps(score["top_drivers"]),
                json.dumps(evidence),
                brief,
                str(score.get("model_version", "1.0")),
            ),
        )
        return int(cur.lastrowid)


def list_assessments(limit: int = 100, path: Path | str = DB_PATH) -> list[dict]:
    init_db(path)
    with connect(path) as conn:
        rows = conn.execute(
            "SELECT * FROM assessments ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
    return [dict(r) for r in rows]
