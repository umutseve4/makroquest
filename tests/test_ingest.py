"""M1.2 ingestion tests — no network: fixture payloads + in-memory SQLite."""

import pytest

from makroquest.ingest.sources import SERIES, fetch_series, parse_wb_payload
from makroquest.ingest.storage import connect, count_observations, upsert_observations

WB_FIXTURE = [
    {"page": 1, "pages": 1, "per_page": 100, "total": 3},
    [
        {"date": "2023", "value": 53.86, "indicator": {"id": "FP.CPI.TOTL.ZG"}},
        {"date": "2022", "value": 72.31, "indicator": {"id": "FP.CPI.TOTL.ZG"}},
        {"date": "2021", "value": None, "indicator": {"id": "FP.CPI.TOTL.ZG"}},
    ],
]


def fake_fetch(url, params):
    assert "TUR" in url
    assert params["format"] == "json"
    return WB_FIXTURE


def test_parse_skips_null_values_and_sorts():
    rows = parse_wb_payload(WB_FIXTURE)
    assert rows == [("2022", 72.31), ("2023", 53.86)]


def test_parse_rejects_bad_shape():
    with pytest.raises(ValueError):
        parse_wb_payload({"not": "a list"})


def test_fetch_series_uses_fetcher():
    rows = fetch_series("FP.CPI.TOTL.ZG", fetch=fake_fetch)
    assert len(rows) == 2
    assert all(isinstance(v, float) for _, v in rows)


def test_upsert_is_idempotent():
    conn = connect(":memory:")
    rows = [("2022", 72.31), ("2023", 53.86)]
    upsert_observations(conn, "cpi_inflation", rows)
    upsert_observations(conn, "cpi_inflation", rows)  # second run
    assert count_observations(conn, "cpi_inflation") == 2


def test_upsert_updates_revised_value():
    conn = connect(":memory:")
    upsert_observations(conn, "cpi_inflation", [("2023", 53.0)])
    upsert_observations(conn, "cpi_inflation", [("2023", 53.86)])  # revision
    cur = conn.execute(
        "SELECT value FROM observations WHERE series_code=? AND period=?",
        ("cpi_inflation", "2023"),
    )
    assert cur.fetchone()[0] == 53.86


def test_all_series_codes_defined():
    assert len(SERIES) == 5
    assert all(code.strip() for code in SERIES.values())
