"""Idempotent local storage for ingested observations (SQLite).

Postgres (Neon) adapter will reuse the same schema when DATABASE_URL lands.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    series_code TEXT NOT NULL,
    period      TEXT NOT NULL,
    value       REAL NOT NULL,
    source      TEXT NOT NULL DEFAULT 'worldbank',
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (series_code, period)
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute(SCHEMA)
    return conn


def upsert_observations(
    conn: sqlite3.Connection,
    series_code: str,
    rows: list[tuple[str, float]],
) -> int:
    """Insert-or-replace rows. Running twice yields the same row count."""
    now = datetime.now(UTC).isoformat()
    conn.executemany(
        "INSERT INTO observations (series_code, period, value, ingested_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(series_code, period) DO UPDATE SET "
        "value = excluded.value, ingested_at = excluded.ingested_at",
        [(series_code, p, v, now) for p, v in rows],
    )
    conn.commit()
    return len(rows)


def count_observations(conn: sqlite3.Connection, series_code: str | None = None) -> int:
    if series_code:
        cur = conn.execute(
            "SELECT COUNT(*) FROM observations WHERE series_code = ?", (series_code,)
        )
    else:
        cur = conn.execute("SELECT COUNT(*) FROM observations")
    return int(cur.fetchone()[0])
