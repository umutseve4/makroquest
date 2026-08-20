"""CLI: python -m makroquest.ingest [db_path]"""

from __future__ import annotations

import sys
from pathlib import Path

from makroquest.ingest.sources import SERIES, fetch_all
from makroquest.ingest.storage import connect, count_observations, upsert_observations


def main(db_path: str = "data/makroquest.db") -> int:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    data = fetch_all()
    for name, rows in data.items():
        n = upsert_observations(conn, name, rows)
        print(f"{name:15s} ({SERIES[name]}): {n} rows upserted")
    total = count_observations(conn)
    print(f"TOTAL observations in db: {total}")
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
