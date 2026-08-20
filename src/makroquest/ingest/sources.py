"""Data sources for MakroQuest.

World Bank Indicators API — keyless, JSON, stable.
Docs: https://datahelpdesk.worldbank.org/knowledgebase/topics/125589
"""

from __future__ import annotations

from typing import Any, Callable

import httpx

WB_BASE = "https://api.worldbank.org/v2/country/TUR/indicator/{code}"

#: Series tracked by the game (World Bank indicator codes, annual, Türkiye).
SERIES: dict[str, str] = {
    "cpi_inflation": "FP.CPI.TOTL.ZG",       # TÜFE enflasyonu, yıllık %
    "unemployment": "SL.UEM.TOTL.ZS",        # İşsizlik oranı, %
    "fx_usd_try": "PA.NUS.FCRF",             # Resmî USD/TRY kuru
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",       # Reel GSYH büyümesi, %
    "gdp_usd": "NY.GDP.MKTP.CD",             # GSYH, cari USD
}

Fetcher = Callable[[str, dict[str, Any]], Any]


def _default_fetch(url: str, params: dict[str, Any]) -> Any:
    resp = httpx.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_wb_payload(payload: Any) -> list[tuple[str, float]]:
    """Parse a World Bank API JSON payload into [(period, value), ...].

    Payload shape: [metadata, [ {date, value, ...}, ... ]].
    Rows with null values are skipped; non-numeric values raise ValueError.
    """
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("unexpected World Bank payload shape")
    rows = payload[1] or []
    out: list[tuple[str, float]] = []
    for row in rows:
        period = str(row.get("date", "")).strip()
        value = row.get("value")
        if not period:
            raise ValueError(f"row missing date: {row!r}")
        if value is None:
            continue  # gap in the series — skip, do not fabricate
        out.append((period, float(value)))
    out.sort(key=lambda t: t[0])
    return out


def fetch_series(
    indicator_code: str,
    fetch: Fetcher | None = None,
    per_page: int = 100,
) -> list[tuple[str, float]]:
    """Fetch one indicator for Türkiye. Returns [(period, value), ...]."""
    fetch = fetch or _default_fetch
    url = WB_BASE.format(code=indicator_code)
    payload = fetch(url, {"format": "json", "per_page": per_page})
    return parse_wb_payload(payload)


def fetch_all(fetch: Fetcher | None = None) -> dict[str, list[tuple[str, float]]]:
    """Fetch every tracked series. Returns {series_name: rows}."""
    return {name: fetch_series(code, fetch=fetch) for name, code in SERIES.items()}
